from django.contrib.auth.forms import UserCreationForm
from django import forms

from django.contrib.auth import get_user_model
from .models import Post, Comment


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User

class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'location', 'category', 'image')
        # Чтобы форма работала как раньше — нужно указать,  что для поля с датой рождения используется виджет с типом данных date.
        widgets = {
                'pub_date': forms.DateTimeInput(attrs={'type':'datetime-local', 'class':'form-control'})
            }


class UserUpdateForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)