from django.db.models import Count
from django.utils.timezone import now


def annotate(queryset):
    queryset = queryset.select_related(
        'author',
        'category',
        'location',
    ).order_by('-pub_date').annotate(
        comment_count=Count('comments')
    )
    return queryset


def filter(queryset):
    queryset = queryset.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    )
    return queryset
