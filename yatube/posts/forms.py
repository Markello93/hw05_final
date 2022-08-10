from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        group = forms.CharField(required=False)
        fields = ('group', 'text', 'image')
        help_texts = {
            'group': 'Группа, к которой относится пост',
            'text': 'Текст Вашего поста',
            'image': 'Прикрепить изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Текст комментария'}
