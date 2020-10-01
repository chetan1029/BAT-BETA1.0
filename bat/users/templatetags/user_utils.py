from django import template

register = template.Library()

@register.filter
def formattedRoleName(role):
    return ''.join(x.capitalize() + ' ' or '_' for x in role.split('_'))