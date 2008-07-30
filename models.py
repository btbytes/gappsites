from google.appengine.ext import db
from google.appengine.api import urlfetch
import urllib


def get_apikey():
    f = open('apikey.txt', 'r')
    apikey = f.readline().strip()
    f.close()
    return apikey
    
class Tag(db.Model):
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)
    
    def incr_ecount(self):
        self.entrycount +=1
        
    def decr_ecount(self):
        if self.entrycount > 0:
            self.entrycount -= 1
            
        
class WebSite(db.Model):
    author = db.UserProperty()
    title = db.StringProperty(required=True)
    link = db.LinkProperty(required=True)
    description = db.TextProperty(required=True)
    tags = db.ListProperty(db.Category)
    srclink = db.StringProperty() #XXX
    is_public = db.BooleanProperty(required=True, default=False)
    screencap = db.BlobProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    deschtml = db.TextProperty()
    likedby = db.StringListProperty()
    votes = db.IntegerProperty(default=0)
    
    def get_tags(self):
        return ' '.join([urllib.unquote(tag) for tag in self.tags])
  
    def set_tags(self, tags):
        if tags:
            tags = tags.strip(' ')
            tags = [db.Category(urllib.quote(tag.strip())) for tag in tags.split(' ')]
            self.tags = [tag for tag in tags if not tag in self.tags]
  
    tags_spc = property(get_tags,set_tags)

    def update_tags(self,update):
        if self.tags: 
            for tag in self.tags:
                tag_ = urllib.unquote(tag)
                tags = Tag.all().filter('tag',tag_).fetch(1) 
                if tags == []:
                    tagnew = Tag(tag=tag_,entrycount=1)
                    tagnew.put()
                else:
                    if not update:
                        tags[0].entrycount+=1
                        tags[0].put()

    def save(self):
        self.update_tags(False)
        self.put()
        
    def update_vote(self, user):
        if user.nickname() not in self.likedby and user != self.author:
            self.votes = self.votes + 1
            self.likedby.append(user.nickname()) 
            self.put()
            return True
        else: return False
        
    def update_screencap(self):
        url = 'http://images.websnapr.com/?size=M&key=%s&url=%s' % (get_apikey(), self.link)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            self.screencap = db.Blob(result.content)
            self.put()
    
            
