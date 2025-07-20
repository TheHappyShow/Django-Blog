from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    print("Фильтр add_class загружен!")
    return field.as_widget(attrs={"class": css})