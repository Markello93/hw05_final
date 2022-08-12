from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import UniqueConstraint

from .constants import POST_STRING_SIZE

User = get_user_model()


class Group(models.Model):
    """Класс Group определеяет ключевые
    параметры группы постов.
    """

    title = models.CharField(
        verbose_name='Титул группы',
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name='Ссылка группы',
        unique=True,
    )
    description = models.TextField(
        verbose_name='Описание группы',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    """Класс Post используется для задания
    параметров отображения постов на сайте.
    """

    text = models.TextField(
        verbose_name='Текст поста',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Имя автора',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Название группы',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
    )

    image = models.ImageField('Картинка', upload_to='posts/', blank=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:POST_STRING_SIZE]


class Comment(models.Model):
    """Класс Comment определеяет ключевые
    параметры комментариев к постам.
    """

    post = models.ForeignKey(
        Post,
        verbose_name='Ссылка на пост',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(verbose_name='Текст комментария')
    author = models.ForeignKey(
        User,
        verbose_name='Имя автора',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:POST_STRING_SIZE]


class Follow(models.Model):
    """Класс Follow определеяет ключевые
    параметры системы подписки на авторов.
    """

    user = models.ForeignKey(
        User,
        verbose_name='Имя подписчика',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Имя автора',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        UniqueConstraint(name='unique_following', fields=['user', 'author'])
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
