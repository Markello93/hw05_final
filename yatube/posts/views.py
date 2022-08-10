from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import page_posts_paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    """View-метод вывода постов на главной странице."""
    posts = Post.objects.all()

    context = {
        'page_obj': page_posts_paginator(request, posts),
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View-метод вывода заданных групп постов.
    Использует выборку объектов из модели Post,
    передает информацию из БД в шаблон."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')

    context = {
        'group': group,
        'page_obj': page_posts_paginator(request, posts),
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """View-метод вывода данных о пользователе.
    Вывыодит общее количество постов, имя пользователя.
    """
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user.id, author=author).exists()
    context = {
        'author': author,
        'page_obj': page_posts_paginator(request, posts),
        'following': following
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Функция позволяющая получить информацию о посте"""
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'group',
        ),
        pk=post_id,
    )
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция создания поста"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)

    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Функция редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }

    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    """Функция добавления комментария"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Функция перехода на страницу подписок"""
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': page_posts_paginator(request, posts),
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Функция подписки на автора"""
    user = request.user
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=user, author=author)
    if user != author and not follower.exists():
        Follow.objects.create(user=user, author=author)

    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    """Функция отписки от автора"""
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()

    return redirect('posts:profile', username=author)
