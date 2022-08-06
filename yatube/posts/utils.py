from django.core.paginator import Paginator

from .constants import PAGIN_PAGES


def paginator(request, posts):
    """Функция paginator позволяет настроить вывод
    требуемого количества постов на страницу,
    количество указано в константе PAGIN_PAGES."""
    paginator = Paginator(posts, PAGIN_PAGES)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
