from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^qq/authorization/$', views.OauthLoginView.as_view()),
    url(r'^qq/user/$', views.OauthView.as_view()),
    url(r'^sina/authorization/$',views.OauthWeiboLoginView.as_view()),
    url(r'^sina/user/$',views.WbOauthView.as_view()),
]
