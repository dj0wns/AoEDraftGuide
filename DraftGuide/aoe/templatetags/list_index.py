from django import template

register = template.Library()

@register.filter
def index(value, arg):
  if arg < len(value): 
    return value[arg]
  else:
    return ""
