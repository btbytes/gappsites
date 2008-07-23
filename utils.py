from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
import os
import functools
import unicodedata
import re


    
class BaseRequestHandler(webapp.RequestHandler):    
    def __init__(self,**kw):
        webapp.RequestHandler.__init__(BaseRequestHandler, **kw)

    def render(self, tmpl, **kw):
        template_values = dict(**kw)
        template_values.update({'user': users.get_current_user()})
        template_values.update({'users': users})
        template_values.update({'site': type(self.request.headers['Host'])})
        path = os.path.join(os.path.dirname(__file__), 'templates',tmpl)
        self.response.out.write(template.render(path, template_values))


def login_required(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        else:
            return method(self, *args, **kwargs)
    return wrapper


def administrator(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            if self.request.method == "GET":
                self.redirect(users.create_login_url(self.request.uri))
                return
        if not users.is_current_user_admin():
            raise webapp.Error(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper


def slugify(s):
    ''' 
    >>> slugify("Hello world !")
    'hello_world'
    '''
    s = re.sub('\s+', '_', s)
    s = re.sub('[^\w.-]', '', s)
    return s.strip('_.- ').lower()

def unique(lst):
    d = {}
    for item in lst:
        d[item] = 1
    return d.keys()