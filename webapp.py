from cgi import escape
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from models import WebSite, Tag
from utils import BaseRequestHandler, administrator, login_required, slugify, unique
from lib import markdown2

template.register_template_library('gapptags')


class HomePage(BaseRequestHandler):
    def get(self):
        websites = WebSite.gql('WHERE is_public=True ORDER BY created DESC')
        self.render('index.html', websites=websites)

class ShowTagged(BaseRequestHandler):
    def get(self,tagname):
        result = Tag.all().filter('tag', tagname).filter('valid', True)
        tag = result.fetch(limit=1)
        if len(tag) > 0:
            tagname = tag[0].tag
            if users.is_current_user_admin():
                websites = WebSite.all().filter('tags', tagname).order('-created')
            else:
                websites = WebSite.all().filter('tags', tagname).filter('is_public', True).order('-created')
            self.render('tag.html', tag=tagname, websites=websites)
        else:
            self.render('base.html', message='No Such Tag')
            
            
class SubmitSite(BaseRequestHandler):
    @login_required
    def get(self):
        self.render('submit.html')
    @login_required    
    def post(self):
        author = users.get_current_user()
        title = escape(self.request.get("title"))
        link = escape(self.request.get("link"))
        description = escape(self.request.get("description"))
        tagsrc = self.request.get("tagsrc")
        srclink = escape(self.request.get("srclink"))
        deschtml = markdown2.markdown(description)
        tags = tagsrc.split(' ')
        
        ws = WebSite(author=author, title=title, link=link,
            description=description, srclink=srclink, is_public=False,
            deschtml=deschtml)
        ws.update_screencap()
        ws.tags_spc = tagsrc
        ws.save()
        self.render('submit_success.html')
        
class MostCommented(BaseRequestHandler):
    def get(self):
        self.render('most-commented.html')

class HighestRated(BaseRequestHandler):
    def get(self):
        websites = WebSite.gql('WHERE is_public=True ORDER BY votes DESC LIMIT 5')
        self.render('highest-rated.html', websites=websites)


class WithSource(BaseRequestHandler):
    def get(self):
        websites = WebSite.gql('WHERE is_public=True  ORDER BY created ')
        self.render('with-source.html')
    
class About(BaseRequestHandler):
    def get(self):
        self.render('about.html')

class UserProfile(BaseRequestHandler):
    def get(self, userid):
        websites = WebSite.gql('WHERE is_public=True  and author=:1 ORDER BY created DESC ', userid)
        self.render('userprofile.html', websites=websites)
    
class ReviewSites(BaseRequestHandler):
    def get(self):
        websites = WebSite.gql('WHERE is_public=False ORDER BY created ')
        self.render('reviewsites.html', websites=websites)
        
class LoginHandler(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.redirect('/')

class LogoutHandler(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect('/')

class Image (webapp.RequestHandler):
    def get(self,img_id):
        website = db.get(img_id)
        if website.screencap:
            self.response.headers['Content-Type'] = "image/jpg"
            self.response.out.write(website.screencap)
        else:
            self.error(404)

class DisplayWebSite(BaseRequestHandler):
    def get(self, ws_id):
        website = db.get(ws_id)
        self.render('website.html', website=website)
      
class ShowWebSite(BaseRequestHandler):
    @administrator
    def get(self, ws_id):
        website = db.get(ws_id)
        website.is_public=True
        website.put()
        self.render('website.html', website=website)


class HideWebSite(BaseRequestHandler):
    @administrator
    def get(self, ws_id):
        website = db.get(ws_id)
        website.is_public=False
        #invalidate the tags?
        tags = website.get_tags()
        newtags = []
        
        for t in tags:
            if WebSite.all().filter('tags', t).count() > 1:
                tg = Tag.all().filter('tag',tag).fetch(1)
                if len(tg)>1: 
                    newtags.append(t)
                    if tg[0].entrycount > 0:
                        tg[0].entrycount -= 1
                        tg[0].put()
                        
        newtags = [t for t in newtags if t != ' ']
        website.tags_spc = ' '.join(newtags)
        website.put()
        self.render('website.html', website=website)
  
class VoteUpWebSite(BaseRequestHandler):
    @login_required
    def get(self, ws_id):
        website = db.get(ws_id)
        user = users.get_current_user()
        if website.update_vote(user): 
            message = 'Thanks for the vote'
        else:
            message = 'Looks like you have already voted'
            
        self.render('website.html', website=website, message=message)
     
class UpdateThumbnail(BaseRequestHandler):
    @administrator
    def get(self, ws_id):
        website = db.get(ws_id)
        website.update_screencap()
        message = "Thumbnail updated"
        self.render('website.html', website=website, message=message)
        
def main():
  application = webapp.WSGIApplication(
        [(r'/$', HomePage),
         (r'/img/(.*).jpg', Image),
         (r'/s/([-\w]+)/$', DisplayWebSite),
         (r'/hide/([-\w]+)/$', HideWebSite),
         (r'/show/([-\w]+)/$', ShowWebSite),
         (r'/voteup/([-\w]+)/$', VoteUpWebSite),
         (r'/tag/([-\w]+)/$', ShowTagged),
         (r'/login/', LoginHandler),
         (r'/logout/', LogoutHandler),
         (r'/most-comments/', MostCommented),
         (r'/highest-rated/', HighestRated),
         (r'/with-source/', WithSource),
         (r'/newthumb/([-\w]+)/$', UpdateThumbnail),
         (r'/about/', About),
         (r'/submit/', SubmitSite),
         (r'/user/(.*)/$', UserProfile),
         (r'/review/', ReviewSites),
         ],
        debug=True)
  wsgiref.handlers.CGIHandler().run(application)
  
if __name__ == "__main__":
  main()