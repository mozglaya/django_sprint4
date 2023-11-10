from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Post, Comment, User


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput
            (attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'format': "%d/%m/%Y %H:%M:%S",
            }
            )
        }

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['pub_date'].input_format = ['%d/%m/%Y %H:%M:%S']
# Не уверена, что так правильно,
# но при нажатии на виджет можно выбрать "Сегодня" и все отображается верно.


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)
        exclude = ('password',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
