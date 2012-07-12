from django.db import models
from django.contrib.auth.models import User

class Link(models.Model):
    url = models.URLField(unique=True)
    
    def __unicode__(self):
        return self.url

class Bookmark(models.Model):
    user = models.ForeignKey(User)
    link = models.ForeignKey(Link)
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return u'%s, %s' % self.user.username, self.link.url

class Tag(models.Model):
    name = models.CharField(unique=True, max_length=40)
    bookmarks = models.ManyToManyField(Bookmark)
    
    def __unicode__(self):
        return self.name
