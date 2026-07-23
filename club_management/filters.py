from datetime import datetime, date


def format_date(value):
    if not value:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%B %d, %Y')
    return str(value)


def format_time(value):
    if not value:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime('%I:%M %p')
    return str(value)
