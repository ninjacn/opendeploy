from django import template
from opendeploy import settings

register = template.Library()

@register.simple_tag
def show_version():
    return settings.VERSION
