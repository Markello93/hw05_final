from http import HTTPStatus

import shutil
import tempfile
import hashlib

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..constants import POST_STRING_SIZE
from ..forms import PostForm
from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    """Тесты проверки forms.py для приложения posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Рандомный текст',
            slug='test-slug',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.small_gif_sha256 = hashlib.sha256(cls.small_gif).hexdigest()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Ж' * POST_STRING_SIZE,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_auth_user_can_published_new_post(self):
        """Авторизированный пользователь может публиковать посты."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='RollerCoaster.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'author': self.author,
            'text': "Testing test",
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'author'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        with open(post.image.path, 'rb') as f:
            file_bytes = f.read()
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        self.assertEqual(self.small_gif_sha256, file_sha256)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.image, 'posts/' + form_data['image'].name)

    def test_text_label_for_new_post(self):
        """Тестирование формы заполнения текста при создания нового поста."""
        title_label = self.form.fields['text'].label
        self.assertEqual(title_label, 'Текст поста')

    def test_group_label_for_new_post(self):
        """Тестирование формы группы при создания нового поста"""
        title_label = self.form.fields['group'].label
        self.assertEqual(title_label, 'Название группы')

    def test_auth_user_can_edit_post(self):
        """Авторизированный пользователь может редактировать посты."""
        uploaded = SimpleUploadedFile(
            name='MyNewGif.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Что-то уникальное!!!!',
            'group': self.group.id,
            'image': uploaded,
        }
        post = Post.objects.first()
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_edited = Post.objects.get(pk=post.id)
        with open(post_edited.image.path, 'rb') as f:
            file_bytes = f.read()
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        self.assertEqual(self.small_gif_sha256, file_sha256)
        self.assertEqual(post_edited.text, form_data['text'])
        self.assertEqual(post_edited.group.id, form_data['group'])
        self.assertEqual(
            post_edited.image.name, 'posts/' + form_data['image'].name
        )

    def test_auth_user_can_comment_post(self):
        """Тестирование добавления комментария для авторизированного юзера"""
        numb_of_comments = Comment.objects.count()
        form_data = {'text': 'Комментарий'}
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), numb_of_comments + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.author.id, self.author.id)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post.id, self.post.id)

    def test_anon_user_cant_comment_post(self):
        """Тестирование, неавторизированный пользователь
        не может добавить коммент"""
        numb_of_comments = Comment.objects.count()
        form_data = {'text': 'Комментарий'}
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), numb_of_comments)

    def test_anon_user_cant_create_post(self):
        """Тестирование, неавторизированный пользователь
        не может создать пост"""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif', content=self.small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'Что-то уникальное',
            'group': self.group.id,
            'image': uploaded,
        }

        self.client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count)

    def test_anon_user_cant_edit_post(self):
        """Тестирование, неавторизированный пользователь
        не может отредактировать пост"""
        uploaded = SimpleUploadedFile(
            name='small.gif', content=self.small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'Пытаемся отредактировать пост',
            'group': self.group.id,
            'image': uploaded,
        }

        self.assertNotEqual(self.post.text, form_data['text'])
