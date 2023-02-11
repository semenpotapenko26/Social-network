from django.test import TestCase, Client
from posts.models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',

        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_guest(self):
        '''Страница доступна и использует корректный
        шаблон для неавторизованного клиента'''
        templates_urls_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={
                    'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={
                    'username': 'user'}): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk}): 'posts/post_detail.html',
        }

        for url, template in templates_urls_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_login(self):
        '''Страница доступна и использует
        корректный шаблон для авторизованного клиента'''
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_uses_correct_template_author(self):
        '''Страница доступна и использует
        корректный шаблон для автора'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}))
        self.assertEqual(self.user, self.post.author)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_uses_uncorrect_template(self):
        '''Проверка ошибки 404 при вводе несуществуещего адреса'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comments_detail_url_exists_at_desired_location_authorized(self):
        '''Проверка, что комментировать посты
        может только авторизованный пользователь'''
        response = self.authorized_client.get(reverse(
            'posts:add_comment', kwargs={
                'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
