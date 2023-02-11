from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.forms import CreationForm
from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create(
            first_name='Дима',
            last_name='Тест',
            username='dimaPotapenko',
            email='azary@yandex.ru',
        )
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_user_create_signup(self):
        """Валидная форма создает пользователя в базе данных."""
        user_count = User.objects.count()
        form_data = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'SemPotapenko',
            'email': 'azar@yandex.ru',
            'password1': 'Changeme4116',
            'password2': 'Changeme4116',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
