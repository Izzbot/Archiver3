from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.url_list, name='url_list'),
    url(r'^url/(?P<pk>[0-9]+)/$', views.url_detail, name='url_detail'),
    url(r'^url/new/$', views.url_new, name='url_new'),
    url(r'^url/(?P<pk>[0-9]+)/delete/$', views.url_delete, name='url_delete'),

    # authentication urls
    url(r'^accounts/login/$', auth_views.login),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page':'/lab3'}),

    # api urls
    url(r'^api/$', views.api_url_list.as_view(), name='api_url_list'),
    url(r'^api/(?P<pk>[0-9]+)/$', views.api_url_detail.as_view(), name='api_url_detail'),
    url(r'^api/(?P<pk>[0-9]+)/recapture/$', views.api_url_recapture.as_view(), name='api_url_recapture'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
