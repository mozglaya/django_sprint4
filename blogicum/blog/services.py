from django.db.models import Count
from django.utils.timezone import now


def annotate_post_with_comments(queryset):
    return queryset.select_related(
        'author',
        'category',
        'location',
    ).order_by('-pub_date').annotate(
        comment_count=Count('comments')
    )


def filter_posted_posts(queryset):
    return queryset.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    )
