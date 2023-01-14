from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user('Random_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(title='Test_group', slug='Test_group')

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост в тестовой группе',
        )
        cls.urls = {'index': '/',
                    'group': f'/group/{cls.group.slug}/',
                    'profile': f'/profile/{cls.user.username}/',
                    'post': f'/posts/{cls.post.pk}/',
                    'post_edit': f'/posts/{cls.post.pk}/edit/',
                    'post_create': '/create/',
                    'follow': '/follow/'
                    }

    def test_url_exists_at_desired_location_for_authorized_users(self):
        """Страницы доступны авторизованным пользователям"""
        for url in self.urls.values():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_for_anonymous_users(self):
        """Страницы доступны анонимным пользователям"""
        urls = (
            'index', 'group', 'profile', 'post')
        urls_list = [self.urls[name] for name in urls]
        for url in urls_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def tests_redirect_anonymous_users(self):
        """Проверка переадресации анонимных пользователей"""
        redirect_addresses = {
            self.urls['post_create']: f'{reverse("users:login")}?next='
                                      f'{reverse("posts:post_create")}',
            self.urls['post_edit']:
                reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        }
        for address, redirect_address in redirect_addresses.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def tests_unexciting_page_not_found(self):
        """Тест несуществующей страницы"""
        response = self.authorized_client.get('/unexciting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        urls_templates_names = {
            self.urls['index']: 'posts/index.html',
            self.urls['group']: 'posts/group_list.html',
            self.urls['profile']: 'posts/profile.html',
            self.urls['post']: 'posts/post_detail.html',
            self.urls['post_edit']: 'posts/create_post.html',
            self.urls['post_create']: 'posts/create_post.html',
            'not_exists': 'core/404.html',
            self.urls['follow']: 'posts/follow.html',
        }
        for address, template in urls_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
