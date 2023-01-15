import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Random_user')
        cls.anonim_client = Client()
        cls.authorized_client = Client()
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
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(title='Test_group',
                                         slug='Test_group')
        cls.post = Post.objects.create(author=cls.user,
                                       text='Пост2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        post_count = Post.objects.count()

        form_data = {'text': 'Пост',
                     'group': self.group.id,
                     'image': self.uploaded,
                     }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, 'posts/image.gif')

    def test_edit_post(self):
        pk = self.post.pk
        post_count = Post.objects.count()
        form_data = {
            'text': 'Изм.пост',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': pk}),
            data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': pk}))
        self.assertEqual(Post.objects.count(), post_count)
        post = Post.objects.get(pk=pk)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)

    def test_not_authorized_client_cant_create_post(self):
        """Проверка того, что анонимные посетители не могут создавать посты"""
        post_count = Post.objects.count()
        form_data = {'text': 'Пост',
                     'group': self.group.id,
                     }
        response = self.anonim_client.post(reverse('posts:post_create'),
                                           data=form_data, follow=True)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, f'{reverse("users:login")}?next='
                                       f'{reverse("posts:post_create")}')

    def test_authorized_client_can_create_comment(self):
        """Авторизованный пользователь может оставить коммент"""
        post_pk = self.post.pk
        comments_count = self.post.comments.count()
        form_data = {'text': 'коммент'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_pk}),
            data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': post_pk}))
        self.assertEqual(self.post.comments.count(), comments_count + 1)
        comment = self.post.comments.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_not_authorized_client_cat_create_comment(self):
        """Не авторизованный пользователь НЕ может оставить коммент"""
        comments_count = self.post.comments.count()
        form_data = {'text': 'коммент'}
        response = self.anonim_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True)
        self.assertEqual(self.post.comments.count(), comments_count)
        self.assertRedirects(
            response, f'''{reverse("users:login")}?next={
            reverse("posts:add_comment",
                    kwargs={"post_id": self.post.pk})}''')
