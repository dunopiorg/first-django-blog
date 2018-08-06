from django.conf.urls import url
from . import views
from django.contrib.auth.views import (
    login, logout, password_reset, password_reset_done, password_reset_confirm, 
    password_reset_complete
)

urlpatterns = [
    url(r'^gameid/$', views.get_article),
    url(r'^publish/$', views.set_article, name='publish'),
    url(r'^get_article/$', views.get_article_v2),
    url(r'^test/$', views.test),
    url(r'^test_player/(?P<x>\d+)$', views.test_2),
    url(r'^set_rds_database/$', views.set_rds_database),
    url(r'^$', views.post_list, name='post_list'),
    url(r'^home$', views.home),
    url(r'^login/$', login, {'template_name': 'blog/login.html'}),
    url(r'^logout/$', logout, {'template_name': 'blog/logout.html'}),
    url(r'^register/$', views.register, name='register'),
    url(r'^profile/$', views.view_profile, name='view_profile'),
    url(r'^profile/edit/$', views.edit_profile, name='edit_profile'),
    url(r'^change-password/$', views.change_password, name='change_password'),
    url(r'^reset-password/$', password_reset, name='password_reset'),
    url(r'^reset-password/done/$', password_reset_done, name='password_reset_done'),
    url(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset-password/complete/$', password_reset_complete, name='password_reset_complete'),
]

