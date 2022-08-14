from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..constants import PAGIN_PAGES, POSTS_FOR_TESTING
from ..models import Group, Post, Follow, Comment

User = get_user_model()


class PostsPagesTests(TestCase):
    """Тесты проверки views.py для приложения posts"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug',
        )

        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='image.jpg', content=cls.image, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.author, text='Комментарий'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='user')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон ."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_user.get(reverse('posts:index'))
        self.correct_context_for_functions(response)

    def test_post_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.correct_context_for_functions(response)

        group = response.context['group']
        self.assertEqual(group, self.group)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        self.correct_context_for_functions(response)
        author = response.context['author']
        self.assertEqual(author, self.author)
        following = response.context['following']
        self.assertFalse(following)
        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username},
            )
        )
        new_response = self.authorized_user.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        following = new_response.context['following']
        self.assertTrue(following)

    def correct_context_for_functions(self, response):
        """Унифицированный тест для проверки получения требуемого
        ключа объекта из словаря контекста,
        проверяет получение страницы или  отдельного поста"""
        if response.context.get('page_obj'):
            post = response.context['page_obj'][0]
        else:
            response.context.get('post')
            post = response.context['post']
        context_objects = {
            self.post.author: post.author,
            self.post.text: post.text,
            self.post.group: post.group,
            self.post.id: post.id,
            self.post.image: post.image,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_detail_context(self):
        """Шаблон Post_detail сформирован с правильным контекстом"""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.correct_context_for_functions(response)
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        comments = response.context['comments'][0]
        self.assertEqual(self.comment, comments)

    def test_post_create_show_correct_context_in_edit(self):
        """Шаблон post_create сформирован с правильным контекстом
        для возможности редактировании поста."""
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
            self.assertEqual(response.context.get('is_edit'), True)
            self.assertIsInstance(response.context.get('is_edit'), bool)
            self.correct_context_for_functions(response)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_for_pages(self):
        """Тестирование корректного добавление поста на страницы."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        for address in pages:
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertEqual(
                    response.context.get('page_obj')[0], self.post
                )

    def test_created_post_going_for_his_group(self):
        """Тест-проверка, что пост попадает в группу, к
        которой должен относится."""
        another_group = Group.objects.create(
            title='Тестовый заголовок',
            slug='another-slug',
            description='Тестовое описание',
        )
        response = self.authorized_author.get(
            reverse('posts:group_list', args=[another_group.slug]),
        )
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache_for_index_page(self):
        """Тест проверяющий работу кэширования страницы"""
        index_page = reverse('posts:index')
        response = self.client.get(index_page)
        test_request = response.content
        Post.objects.filter(pk=self.post.id).delete()
        response = self.client.get(index_page)
        self.assertEqual(test_request, response.content)
        cache.clear()
        response = self.client.get(index_page)
        self.assertNotEqual(test_request, response.content)


class PaginatorViewTest(TestCase):
    """Класс тестирования работы шаблона пагинатора
    Создаются фикстуры: клиент и 13 тестовых записей"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        sum_of_posts = PAGIN_PAGES + POSTS_FOR_TESTING
        for i in range(sum_of_posts):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.author,
                group=cls.group,
            )

    def test_first_page_contains_ten_records(self):
        """Первая страница index содержит десять записей."""
        pages_with_pagination = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        for address in pages_with_pagination:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), PAGIN_PAGES
                )

    def test_second_page_contains_three_records(self):
        """Вторая страница index содержит три записи."""
        pages_with_pagination = [
            reverse('posts:index') + '?page=2',
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2',
            reverse('posts:profile', kwargs={'username': self.author})
            + '?page=2',
        ]
        for address in pages_with_pagination:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_FOR_TESTING
                )


class FollowTests(TestCase):
    """Тесты проверки работы механизма подписки на авторов"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.following,
        )

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_following = Client()
        self.authorized_following.force_login(self.following)
        cache.clear()

    def test_auth_user_can_follow_author(self):
        """Тест проверяющий что авторизованный пользователь
        может подписываться на других"""
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following.username},
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )

    def test_auth_user_can_unfollow_author(self):
        """Тест проверяющий что авторизованный пользователь
        может отписаться от автора"""
        Follow.objects.create(user=self.follower, author=self.following)
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following.username},
            )
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )

    def test_subscription_feed_for_auth_users(self):
        """При создании запись появляется в ленте подписчиков автора"""
        Follow.objects.create(user=self.follower, author=self.following)
        response = self.authorized_follower.get('/follow/')
        follower_index = response.context['page_obj'][0]
        self.assertEqual(self.post, follower_index)

    def test_subscription_feed_not_show_own_user_post(self):
        """Тест, если авторизированный пользователь подписан на автора,
        то его собственный пост не появится в его ленте"""
        Follow.objects.create(user=self.follower, author=self.following)
        following_post = Post.objects.create(
            author=self.follower, text='Тестовый текст'
        )
        response = self.authorized_follower.get('/follow/')
        following_index = response.context['page_obj'][0]
        self.assertNotEqual(following_post, following_index)
