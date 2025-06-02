from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def natural_date(value):
    if not value:
        return ""

    today = timezone.localdate()
    date = value.date() if hasattr(value, 'date') else value

    if date == today:
        return "오늘"
    elif date == today - timezone.timedelta(days=1):
        return "어제"
    else:
        return date.strftime("%Y.%m.%d")