from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Category, Comment, Location, Post, User

admin.site.empty_value_display = 'Не задано'

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class AdminUser(BaseUserAdmin):
    @admin.display(description='Кол-во постов у пользователя')
    def posts_count(self, obj):
        return obj.posts.count()

    @admin.display(description='Имя')
    def author_name(self, obj):
        return obj.username

    list_display = (
        'author_name',
        'posts_count',
    )


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'is_published',
        'category',
        'location',
        'author',
        'image_tag',
    )
    list_editable = (
        'is_published',
        'category',
        'location',
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title', 'author',)
    readonly_fields = ['image_tag']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'post',
        'author',
    )
    list_display_links = ('author',)


admin.site.register(Location)
