from django.db.models import Count
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PostForm, UserUpdateForm, CommentForm
from django.urls import reverse_lazy

from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.core.paginator import Paginator
from blog.models import Category, Post, Comment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


User = get_user_model()


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

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


class BirthdayDetailView(DetailView):
    model = Post
    pk_field = 'post_id'
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    post_list = category.posts.filter(is_published=True, pub_date__lte=now()
                                      ).annotate(
                                          comment_count=Count(
                                              'comments'
                                          )).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.profile = get_object_or_404(User,
                                         username=self.kwargs['username'])

        posts = Post.objects.filter(author_id=self.profile.pk
                                    ).prefetch_related(
                                        'location',
                                        'category',
                                        'author',).annotate(
                                            comment_count=Count(
                                                'comments'
                                            )).order_by('-pub_date')
        if self.request.user.get_username() == self.kwargs['username']:
            return posts
        page_obg = posts.filter(
            is_published=True,
            pub_date__lte=now(),
            category__is_published=True
        )
        return page_obg

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'profile': self.profile})
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.last_name = form.cleaned_data['last_name']
        instance.first_name = form.cleaned_data['first_name']
        instance.save()
        return super().form_valid(form)

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


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    parent_post = None

    def dispatch(self, request, *args, **kwargs):
        self.parent_post = get_object_or_404(
            Post,
            pk=kwargs['post_id']
        )
        if request.user != self.parent_post.author:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.post = self.parent_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.parent_post.pk}
        )


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    ...


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):

    def dispatch(self, request, *args, **kwargs):
        self.parent_post = get_object_or_404(
            Post,
            pk=kwargs['post_id'],
            author=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username}
                            )


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


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    comment = None
    parent_post = None

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(
            Comment, pk=kwargs['comment_id'], author=request.user
        )
        self.parent_post = get_object_or_404(
            Post, pk=kwargs['post_id'], is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.parent_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.parent_post.pk}
        )


class CommentDeleteView(
    LoginRequiredMixin, CommentMixin, DeleteView
):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.comment
        context['post'] = self.parent_post
        return context


class CommentUpdateView(
    LoginRequiredMixin, CommentMixin, UpdateView
):
    ...
