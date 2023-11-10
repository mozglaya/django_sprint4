from django.contrib.auth import get_user_model
from django.db import models
from django.utils.safestring import mark_safe

from blog.const import MAX_LENGTH_FIELD as MLF
from blog.const import STR_LENGTH as SL

User = get_user_model()


class CreatedAt(models.Model):
    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ('created_at',)


class PublishedCreatedModel(CreatedAt):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True


class Category(PublishedCreatedModel):
    title = models.CharField('Заголовок', max_length=MLF)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, '
                  'цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:SL]


class Location(PublishedCreatedModel):
    name = models.CharField('Название места', max_length=MLF)

    class Meta(CreatedAt.Meta):
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:SL]


class Post(PublishedCreatedModel):
    title = models.CharField('Заголовок', max_length=MLF)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        null=False,
        help_text='Если установить дату и время '
                  'в будущем — можно делать '
                  'отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Фото',
        upload_to='images',
        blank=True
    )

    def image_tag(self):
        return mark_safe(
            '<img src="/images/%s" width="80" height="60" />' % (self.image)
        )

    image_tag.short_description = 'Image'

    class Meta:
        ordering = ('pub_date',)
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'

    def __str__(self):
        return self.title[:SL]


class Comment(CreatedAt):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
