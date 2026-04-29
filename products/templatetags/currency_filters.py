from django import template

register = template.Library()

@register.filter(name='vn_currency')
def vn_currency(value):
    try:
        # Ép kiểu số và thay dấu phẩy thành dấu chấm
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except (ValueError, TypeError):
        return value