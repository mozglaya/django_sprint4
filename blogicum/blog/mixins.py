from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy

from .models import Post, Comment
from .forms import PostForm, CommentForm


class AuthorCheckMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class PostMixin(LoginRequiredMixin, AuthorCheckMixin):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username}
                            )


class CommentMixin(LoginRequiredMixin, AuthorCheckMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'
    parent_post = None

    def get_success_url(self):
        self.parent_post = get_object_or_404(
            Post, pk=self.kwargs['post_id'], is_published=True
        )
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.parent_post.pk}
        )
