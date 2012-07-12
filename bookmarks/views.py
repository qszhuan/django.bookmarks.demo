from django.http import HttpResponse
from django.template.loader import get_template
from django.template import RequestContext

from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.shortcuts import render_to_response

from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django  import *

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
