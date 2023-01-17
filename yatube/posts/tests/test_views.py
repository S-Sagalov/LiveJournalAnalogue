import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user('Random_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        img = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.gif',
            content=img,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(title='Test_group', slug='Test_group')
        cls.group2 = Group.objects.create(title='Test_group',
                                          slug='Test_group2')
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Пост1',
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='коммент',
        )
        cls.reversed_urls = {
            'index': reverse('posts:index'),
            'group': reverse('posts:group_list',
                             kwargs={'slug': cls.group.slug}),
            'profile': reverse('posts:profile',
                               kwargs={'username': cls.user.username}),
            'post': reverse('posts:post_detail', kwargs={
                'post_id': cls.post.pk}),
            'post_edit': reverse('posts:post_edit', kwargs={
                'post_id': cls.post.pk}),
            'post_create': reverse('posts:post_create'),
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def first_post_check(self, post):
        """Проверка первого поста на стринице"""
        post_fields = {'author': self.user,
                       'group': self.group,
                       'text': self.post.text,
                       'pk': self.post.pk,
                       'image': 'posts/image.gif',
                       }
        for field, value in post_fields.items():
            with self.subTest(field=field):
                self.assertEqual(post.__getattribute__(field), value)

    def test_pages_with_paginator_context(self):
        """Тест страниц с 'множеством' постов"""
        addresses_contexts = {
            self.reversed_urls['index']: {},
            self.reversed_urls['group']: {'group': self.group},
            self.reversed_urls['profile']:
                {'author': self.user, 'posts_count': Post.objects.count()}
        }
        for address, context in addresses_contexts.items():
            response = self.authorized_client.get(address)
            self.first_post_check(response.context['page_obj'][0])
            for attr, value in context.items():
                with self.subTest(attr=attr):
                    self.assertEqual(response.context[attr], value)

    def test_post_detail_show_correct_context(self):
        """Тест страницы конкретного поста"""
        response = self.authorized_client.get(self.reversed_urls['post'])
        self.assertEqual(response.context['posts_count'], Post.objects.count())
        self.first_post_check(response.context['post'])  # проверка всех полей

    def test_post_create_show_correct_context(self):
        """Тест страницы создания поста"""
        response = self.authorized_client.get(
            self.reversed_urls['post_create'])
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField,
                       }

        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Тест страницы редактирования поста"""
        response = self.authorized_client.get(self.reversed_urls['post_edit'])
        form_field_value = response.context.get('form').instance

        self.assertEqual(response.context.get('is_edit'), True)
        self.assertEqual(form_field_value, self.post)

    def test_post_dont_append_another_group(self):
        """Проверка того, что посты не попадают в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_comment_on_post_detail(self):
        """Комментарий появляется на странице поста"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context.get('comments')[0].text,
                         self.comment.text)

    def test_cache(self):
        """Тестирование кэша"""
        response = self.authorized_client.get(self.reversed_urls['index'])
        content1 = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(self.reversed_urls['index'])
        content2 = response.content
        self.assertEqual(content1, content2)
        cache.clear()
        response = self.authorized_client.get(self.reversed_urls['index'])
        content3 = response.content
        self.assertNotEqual(content1, content3)


class PaginatorTest(TestCase):
    POSTS_COUNT = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Random_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(title='Test_group', slug='Test_group')
        Post.objects.bulk_create(
            [Post(author=cls.user, group=cls.group, text=f'Пост{i}') for i in
             range(cls.POSTS_COUNT)])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_paginator(self):
        """Тестирование паджинатора"""
        addresses = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        page_posts_count = settings.PAGINATE_POST_COUNT
        last_page_posts_count = self.POSTS_COUNT % page_posts_count

        for address in addresses:
            response = self.authorized_client.get(address)
            self.assertEqual(len(response.context['page_obj']),
                             page_posts_count)
            response = self.authorized_client.get(
                address + '?page=2')
            self.assertEqual(len(response.context['page_obj']),
                             last_page_posts_count)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user('author')
        cls.follower = User.objects.create_user('follower')
        cls.not_follower = User.objects.create_user('not_follower')

        cls.author_client = Client()
        cls.follower_client = Client()
        cls.not_follower_client = Client()

        cls.author_client.force_login(cls.author)
        cls.follower_client.force_login(cls.follower)
        cls.not_follower_client.force_login(cls.not_follower)

        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_follow(self):
        follow_count_start = Follow.objects.filter(
            user_id=self.not_follower.id).count()
        self.not_follower_client.get(reverse('posts:profile_follow', kwargs={
            'username': self.author.username}))
        follow_count_current = Follow.objects.filter(
            user_id=self.not_follower.id).count()
        self.assertEqual(follow_count_current, follow_count_start + 1)

    def test_unfollow(self):
        Follow.objects.create(author=self.author, user=self.follower)
        follow_count_start = Follow.objects.filter(
            user_id=self.follower.id).count()
        self.follower_client.get(reverse('posts:profile_unfollow', kwargs={
            'username': self.author.username}))
        follow_count_current = Follow.objects.filter(
            user_id=self.not_follower.id).count()
        self.assertEqual(follow_count_current, follow_count_start - 1)

    def test_posts_show_following_users(self):
        Follow.objects.get_or_create(author=self.author, user=self.follower)
        post_text = 'Random_text'
        Post.objects.create(author=self.author, text=post_text)
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(len(response.context.get('page_obj')), 0)
        follow = Follow.objects.get(author=self.author, user=self.follower)
        self.assertEqual(follow.user, self.follower)
        self.assertEqual(follow.author, self.author)
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, post_text)

    def test_posts_dont_show_unfollowing_users(self):
        Post.objects.create(author=self.author, text='Random_text')
        response = self.not_follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context.get('page_obj')), 0)
