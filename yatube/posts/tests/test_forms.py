import http.client

import shutil
import tempfile

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
class TaskPagesTests(TestCase):
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
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Ж' * POST_STRING_SIZE,
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        """Авторизированный пользователь может публиковать посты."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='image.jpg', content=self.image, content_type='image/gif'
        )
        form_data = {
            'text': 'Что-то уникальное',
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
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.image, 'posts/' + uploaded.name)

    def test_text_label(self):
        """Тестирование формы заполнения текста при создания поста."""
        title_label = self.form.fields['text'].label
        self.assertEqual(title_label, 'Текст поста')

    def test_group_label(self):
        """Тестирование формы группы при создания поста"""
        title_label = self.form.fields['group'].label
        self.assertEqual(title_label, 'Название группы')

    def test_edit_post(self):
        """Авторизированный пользователь может редактировать посты."""
        uploaded = SimpleUploadedFile(
            name='image.jpg', content=self.image, content_type='image/gif'
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
        self.assertEqual(response.status_code, http.client.OK)
        post_edited = Post.objects.get(pk=post.id)
        self.assertEqual(post_edited.text, form_data['text'])
        self.assertEqual(post_edited.group.id, form_data['group'])

    def test_post_detail_form(self):
        """Тестирование добавления е комментария"""
        form_data = {'post': self.post, 'text': 'Комментарий'}
        post = Post.objects.first()
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(
            getattr(Comment.objects.latest('created'), 'text'), 'Комментарий'
        )
