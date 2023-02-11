import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from posts.models import Post, Group, Follow
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from posts.forms import PostForm
from http import HTTPStatus

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')
        cls.user_new = User.objects.create(username='user_new')
        cls.user_super_new = User.objects.create(username='user_super_new')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.form = PostForm()
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_super_new
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст из формы',
            'group': PostCreateFormTest.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTest.group.id,
                text='Новый текст из формы',
                image='posts/small.gif'
            ).exists()
        )

    def test_podt_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Новый текст формы',
            'group': PostCreateFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.get(
            pk=self.post.pk).text, 'Новый текст формы')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_client_follow_author(self):
        '''Авторизованный пользователь может подписываться
        на других пользователей.'''
        count_follow = Follow.objects.filter(user=self.user.pk).count()
        data = {
            'user': self.authorized_client,
            'author': self.user_new,
        }
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user_new,)),
            data=data,
            follow=True
        )
        self.assertEqual(Follow.objects.filter(
            user=self.user.pk).count(), count_follow + 1)

    def test_authorized_client_unfollow_author(self):
        '''Авторизованный пользователь может отписываться
        от других пользователей.'''
        count_follow = Follow.objects.filter(user=self.user.pk).count()
        data = {
            'user': self.authorized_client,
            'author': self.user_super_new,
        }
        self.authorized_client.post(
            reverse('posts:profile_unfollow', args=(self.user_super_new,)),
            data=data,
            follow=True
        )
        self.assertEqual(Follow.objects.filter(
            user=self.user.pk).count(), count_follow - 1)
