from google.appengine.ext import webapp
from models import Tag
from django.template import Node

register = webapp.template.create_template_register()

def build_tag_list(parser, token):
    """
    {% get_tag_list %}
    """
    return TagMenuObject()

class TagMenuObject(Node):
    def render(self, context):
        output = ['']
        tags = Tag.all()
        #tags = tags.filter('valid=', True)
        for tag in tags:
            if tag.entrycount >= 1:
                output.append(tag)

        context['all_tags'] = output
        return ''

register.tag('get_tag_list', build_tag_list)
