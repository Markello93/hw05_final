from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Класс AboutAuthorView, обрабатывает GET запрос
    вызова статичного шаблона с информацией об авторе."""

    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Класс AboutAuthorView, обрабатывает GET запрос
    вызова статичного шаблона с информацией об используемых
    технологиях."""

    template_name = 'about/tech.html'
