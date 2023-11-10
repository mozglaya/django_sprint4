from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView
)

from blog.models import Category, Post, Comment, User
from .const import PAGINATOR_LENGTH as PL
from .forms import (
    PostForm, UserUpdateForm, CommentForm, CustomUserCreationForm
)
from .mixins import PostMixin, CommentMixin, AuthorCheckMixin


class RegistrationCreateView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('blog:index')


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PL
    queryset = Post.objects.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    )
# Я не очень поняла, как здесь лучше переписать функции, пока оставила так

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True,
        ).select_related(
            'author',
            'category',
            'location',
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for post in context['object_list']:
            post.comment_count = post.comments.count
        return context


class CategoryListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = PL

    def get_object(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return category

    def get_queryset(self):
        posts = self.get_object().posts.select_related('category').filter(
            is_published=True, pub_date__lte=now(
            )).order_by('-pub_date').annotate(
                comment_count=Count(
                    'comments'
                ))
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['category'] = category
        return context


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = PL

    def get_object(self):
        profile = get_object_or_404(User,
                                    username=self.kwargs['username'])
        return profile

    def get_queryset(self):
        profile = self.get_object()
        posts = profile.posts.filter(
            author_id=profile.pk
        ).select_related(
            'author').prefetch_related(
                'location',
                'category',
                'author',).annotate(
                    comment_count=Count('comments')).order_by('-pub_date')
        if self.request.user.get_username() == self.kwargs['username']:
            return posts
        page_obj = posts.filter(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )
        return page_obj

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
        queryset = self.get_queryset()
        return super().get_object(queryset)

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
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username}
                            )


class PostDetailView(ListView):
    model = Post
    pk_field = 'post_id'
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'
    paginate_by = PL

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if self.request.user != post.author and post.pub_date > now():
            raise Http404
        if self.request.user != post.author and not post.is_published:
            raise Http404
        return post

    def get_queryset(self):
        comments = self.get_object().comments.select_related('author')
        return comments

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['post'] = post
        context['form'] = CommentForm()
        return context


class PostUpdateView(PostMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.get_object().pk}
                            )


class PostDeleteView(PostMixin, DeleteView):
    ...


# class CommentCreate(CommentMixin, CreateView):
#     def form_valid(self, form):
#         form.instance.author = self.request.user
#         form.instance.post = self.get_object()
#         return super().form_valid(form)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)
# Не получилось переписать в класс - вылетает 404


class CommentUpdateView(CommentMixin, AuthorCheckMixin, UpdateView):
    ...


class CommentDeleteView(CommentMixin, DeleteView):
    def get_context_data(self, **kwargs):
        self.comment = get_object_or_404(
            Comment, pk=self.kwargs['comment_id'], author=self.request.user
        )
        context = super().get_context_data(**kwargs)
        context['comments'] = self.comment
        context['post'] = self.parent_post
        return context
