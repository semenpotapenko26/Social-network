from django.core.cache import cache
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.models import Post, Group, Comment, Follow
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.user_new = User.objects.create(username='user_new')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый текст комментария'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_new
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.new_authorized_client = Client()
        self.new_authorized_client.force_login(self.user_new)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={
                    'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={
                    'username': 'user'}): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': self.post.id}): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.group.title
        task_slug_0 = first_object.group.slug
        task_description_0 = first_object.group.description
        self.assertEqual(task_title_0, self.group.title)
        self.assertEqual(task_slug_0, self.group.slug)
        self.assertEqual(task_description_0, self.group.description)

    def test_correct_post_create(self):
        """Проверка, что этот пост не попал в группу,
        для которой не был предназначен."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, self.post.pk)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, self.post.pk)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': 'user'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.pk, self.post.pk)

    def test_pages_show_correct_context(self):
        '''Проверка, что при выводе поста с
        картинкой изображение передаётся в словаре context'''
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0].image
        self.assertEqual(first_object, self.post.image)
        response = self.authorized_client.get(reverse('posts:profile', kwargs={
            'username': 'user'}))
        first_object = response.context['page_obj'][0].image
        self.assertEqual(first_object, self.post.image)
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0].image
        self.assertEqual(first_object, self.post.image)
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post.pk}))
        first_object = response.context['post'].image
        self.assertEqual(first_object, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        '''После успешной отправки комментарий
        появляется на странице поста'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        post = response.context['comments'][0]
        self.assertEqual(post.text, 'Тестовый текст комментария')

    def test_cache_work_correct(self):
        '''Список записей хранится в кеше и обновляется раз в 20 секунд'''
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response = self.authorized_client.get(reverse('posts:index')).content
        post.delete()
        response_1 = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(response, response_1)
        cache.clear()
        response_2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(response_2, response)

    def test_follow_and_delete_correct(self):
        '''Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан..'''
        post = Post.objects.create(
            text='Новый текст из поста',
            author=self.user_new)
        follower = self.authorized_client.get(reverse('posts:follow_index'))
        follower_context = follower.context['page_obj']
        unfollower = self.new_authorized_client.get(
            reverse('posts:follow_index'))
        unfollower_context = unfollower.context['page_obj']
        self.assertIn(post, follower_context)
        self.assertNotIn(post, unfollower_context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(0, 13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group,
            )

    def test_first_page_contains_ten_records_index(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records_index(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_group_list(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records_group_list(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_profile(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': 'user'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records_profile(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': 'user'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
