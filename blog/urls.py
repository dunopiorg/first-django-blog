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
    url(r'^update-template-db/$', views.db_setting_viewer),
    url(r'^plain_articles$', views.get_plain_article),
    url(r'^update-template-db/(?P<db_name>\S+)/$', views.db_setting_viewer),
    url(r'^home$', views.home),
    url(r'^futures/(?P<game_id>\S+)$', views.futures),
    url(r'^refresh/(?P<version>\S+)/(?P<game_id>\S+)$', views.refresh_futures),
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

