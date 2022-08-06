from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..constants import POST_STRING_SIZE
from ..models import Group, Post, Comment

User = get_user_model()


class PostsURLTests(TestCase):
    """Тесты проверки urls.py для приложения posts"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Ж' * POST_STRING_SIZE,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Ж' * POST_STRING_SIZE,
            author=cls.author,
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.user = User.objects.create_user(username='user')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """Тест проверяет правильность прописанных
        шаблонов для генерируемых ссылок на странницы"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_page_with_author(self):
        """Редактирование поста доступно только автору."""
        response = self.authorized_author.get(
            f'/posts/{self.post.id}/edit',
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_url_exists_at_desired_location(self):
        """Тестирование отправки запроса любого
        пользователя к несуществующей странице."""
        response = self.client.get('/group/fanstastic/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_authorized_client_post_create(self):
        """Тестирование наличия у авторизированного пользователя
        иметь доступ к странице создания поста"""
        response = self.authorized_author.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_access(self):
        """Тестирование доступности главной страницы
        для любого пользователю."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_group_slug_access(self):
        """Тестирование возможности просмотреть
        любую группу любому пользователю."""
        response = self.client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_access(self):
        """Тестирование возможности просмотреть
        любой пост любому пользователю."""
        response = self.client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_author_access(self):
        """Тестирование возмоджности просмотреть профиль
        автора для любого пользователя."""
        response = self.client.get(f'/profile/{self.post.author}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous(self):
        """Тест определяющий факт работы редиректа при
        попытке анонимного пользователя отредактировать пост."""
        response = self.client.get(f'/posts/{self.post.id}/edit', Follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit',
        )

    def test_url_redirect_anonymous(self):
        """Тест определяющий факт работы редиректа при
        попытке анонимного пользователя создать пост."""
        response = self.client.get('/create/', Follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_auth_user_edit(self):
        """Тест определяющий факт работы редиректа при
        попытке авторизированного пользователя отредактировать
        чужой пост."""
        response = self.authorized_user.get(
            f'/posts/{self.post.id}/edit/',
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )

    def test_404_url_exists_at_desired_location(self):
        """Проверка запроса к несуществующей странице."""
        response = self.client.get('/group/fanstastic/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment_redirect_anonymous(self):
        """Тест определяющий факт работы редиректа при
        попытке анонимного пользователя оставить комментарий."""
        response = self.client.get(
            f'/posts/{self.post.id}/comment/', Follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

    def test_follow_redirect_anonymous(self):
        """Тест определяющий факт работы редиректа при
        попытке анонимного пользователя подписаться на автора."""
        response = self.client.get(
            f'/profile/{self.author.username}/follow/', Follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/profile/{self.author.username}/follow/',
        )
