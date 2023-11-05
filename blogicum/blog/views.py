from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PostForm, UserUpdateForm, CommentForm
from django.urls import reverse_lazy, reverse

from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView
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
    ordering = '-pub_date'
    paginate_by = 10


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


# def post_detail(request, post_id):
#     post = get_object_or_404(
#         Post,
#         is_published=True,
#         category__is_published=True,
#         pub_date__lte=now(),
#         pk=post_id
#     )
#     context = {'post': post, }
#     return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    post_list = category.posts.filter(
        is_published=True,
        pub_date__lte=now()
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


class ProfileListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = Post.objects.filter(author_id=self.request.user.id).order_by('-pub_date')
        paginator = Paginator(context, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'page_obj': page_obj,
                   'profile': self.request.user.username,
                   'user': self.request.user,
                   }
        return context


class ProfileUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'
    # slug_field = 'username'
    # slug_url_kwarg = 'username'

    # def dispatch(self, request, *args, **kwargs):
    #     get_object_or_404(User, username=request.user)
    #     return super().dispatch(request, *args, **kwargs)
    # def get_success_url(self):
    #     return reverse_lazy('blog:profile',
    #                  kwargs={'username': self.request.user.username})

    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        updated_user = self.get_object()
        username = updated_user.username
        return reverse_lazy('blog:profile',
        kwargs={'username': username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                     kwargs={'username': self.request.user.username})


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    parent_post = None

    def dispatch(self, request, *args, **kwargs):
        self.parent_post = get_object_or_404(Post, pk=kwargs['post_id'])
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
    def get_context_data(self, **kwargs):
        self.parent_post = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().get_context_data(self, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('blog:profile',
        kwargs={'username': self.request.user.username})


@login_required
def add_comment(request, post_id):
    # Получаем объект дня рождения или выбрасываем 404 ошибку.
    post = get_object_or_404(Post, id=post_id)
    # Функция должна обрабатывать только POST-запросы.
    form = CommentForm(request.POST)
    if form.is_valid():
        # Создаём объект поздравления, но не сохраняем его в БД.
        comment = form.save(commit=False)
        # В поле author передаём объект автора поздравления.
        comment.author = request.user
        # В поле birthday передаём объект дня рождения.
        comment.post = post
        # Сохраняем объект в БД.
        comment.save()
    # Перенаправляем пользователя назад, на страницу дня рождения.
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
    # model = Comment
    # form_class = CommentForm
    # template_name = 'blog/comment.html'
    # pk_field = 'comment_id'
    # pk_url_kwarg = 'comment_id'
    ...
    # def dispatch(self, request, *args, **kwargs):
    #     self.comment = get_object_or_404(
    #         Comment, pk=kwargs['comment_id'], author=request.user
    #     )
    #     self.parent_post = get_object_or_404(
    #         Post, pk=kwargs['post_id'], is_published=True
    #     )
    #     return super().dispatch(request, *args, **kwargs)

    # def form_valid(self, form):
    #     form.instance.author = self.request.user
    #     form.instance.post = self.parent_post
    #     return super().form_valid(form)

    # def get_success_url(self):
    #     return reverse_lazy(
    #         'blog:post_detail', kwargs={'post_id': self.parent_post.pk}
    #     )
