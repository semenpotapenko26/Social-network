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
                'users:signup'): 'users/signup.html',
            reverse(
                'users:login'): 'users/login.html',
            reverse(
                'users:password_reset'): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'): 'users/password_reset_done.html',
        }

        for url, template in templates_urls_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_login(self):
        '''Страница доступна и использует
        корректный шаблон для авторизованного клиента'''
        response = self.authorized_client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/logged_out.html')

    def test_urls_uses_correct_template_change_password(self):
        '''Страница доступна и использует
        корректный шаблон для авторизованного клиента изменения пароля'''
        templates_urls_names = {
            reverse(
                'users:password_change'): 'users/password_change_form.html',
            reverse(
                'users:password_change_done'): 'users/'
            'password_change_done.html',
        }

        for url, template in templates_urls_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
