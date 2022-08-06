from django.contrib.auth import get_user_model
from django.test import TestCase

from ..constants import POST_STRING_SIZE
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тесты проверки models.py для приложения posts."""

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
            text='Тестинг' * POST_STRING_SIZE,
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверка корректной работы __str__."""

        check_dict = {
            self.post.text[:POST_STRING_SIZE]: str(self.post),
            self.group.title: str(self.group),
        }

        for model, expected_value in check_dict.items():
            with self.subTest(model=model):
                self.assertEqual(
                    model, expected_value, 'Ошибка метода __str__'
                )
