from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView
)

from blog.models import Category, Post, User
from .const import PAGINATOR_LENGTH as PL
from .forms import (
    PostForm, UserUpdateForm, CommentForm, CustomUserCreationForm
)
from .mixins import PostMixin, CommentMixin, AuthorCheckMixin
from .services import annotate_post_with_comments, filter_posted_posts


class RegistrationCreateView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('blog:index')


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PL
    queryset = annotate_post_with_comments(filter_posted_posts(Post.objects))


class CategoryListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = PL

    def get_object(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        return annotate_post_with_comments(
            filter_posted_posts(self.get_object().posts)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['category'] = category
        return context


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = PL

    def get_object(self):
        return get_object_or_404(
            User,
            username=self.kwargs['username']
        )

    def get_queryset(self):
        profile = self.get_object()
        posts = annotate_post_with_comments(profile.posts)
        if self.request.user != profile:
            posts = filter_posted_posts(posts)
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'profile': self.get_object()})
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:index')


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDetailView(ListView):
    model = Post
    pk_field = 'post_id'
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'
    paginate_by = PL

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs[self.pk_url_kwarg])
        if self.request.user != post.author and (
            post.pub_date > now() or not post.is_published
        ):
            raise Http404
        return post

    def get_queryset(self):
        return self.get_object().comments.select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_object()
        context['form'] = CommentForm()
        return context


class PostUpdateView(PostMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={self.pk_url_kwarg: self.get_object().pk}
        )


class PostDeleteView(PostMixin, DeleteView):
    ...


class CommentCreate(CommentMixin, CreateView):
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return super().form_valid(form)


class CommentUpdateView(CommentMixin, AuthorCheckMixin, UpdateView):
    ...


class CommentDeleteView(CommentMixin, AuthorCheckMixin, DeleteView):
    ...
