from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from mysite import views

urlpatterns = [
    url(r'^$', views.login_redirect, name='login_redirect'),
    url(r'^admin/', admin.site.urls),
    url(r'^blog/', include('blog.urls')),
    url(r'^article/', include('blog.urls')),
]
