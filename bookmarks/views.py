from django.http import HttpResponse
from django.template.loader import get_template
from django.template import RequestContext

from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.shortcuts import render_to_response

from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django  import *
from bookmarks.models import *
from bookmarks.forms import *

def main_page(request):
  return render_to_response('main_page.html', RequestContext(request))

def user_page(request, username):
  try:
    user = User.objects.get(username=username)
  except User.DoesNotExist:
    raise Http404(u'Requested user not found.')
  bookmarks = user.bookmark_set.all()
  variables = RequestContext(request, {'username':username, 'bookmarks':bookmarks})
  return render_to_response('user_page.html', variables)


def logout_page(request):
  logout(request)
  return HttpResponseRedirect('/')

def register_page(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      user = User.objects.create_user(username = form.cleaned_data['username'], password = form.cleaned_data['password1'],
                                      email = form.cleaned_data['email'])
      return HttpResponseRedirect('/')
  else:
    form = RegistrationForm()
  variables = RequestContext(request, {'form':form})
    
  return render_to_response('registration/reg.html', variables)

def bookmark_save_page(request):
  if request.method == 'POST':
    form = BookmarkSaveForm(request.POST)
    if form.is_valid():
      link, dummy = Link.objects.get_or_create(url = form.cleaned_data['url'])
      bookmark, created = Bookmark.objects.get_or_create(user = request.user, link = link)
      bookmark.title = form.cleaned_data['title']

      if not created:
        bookmark.tag_set.clear()
      tagnames = form.cleaned_data['tags'].split()
      for tagname in tagnames:
        tag, dummy = Tag.objects.get_or_create(name=tagname)
        bookmark.tag_set.add(tag)
      bookmark.save()
      return HttpResponseRedirect('/user/%s/' % request.user.username)
  else:
    form = BookmarkSaveForm()

  variables = RequestContext(request, {'form':form})
  return render_to_response('bookmark_save.html', variables)



                                               
