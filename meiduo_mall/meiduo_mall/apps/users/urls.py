from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token


urlpatterns = [
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SmsCodeView.as_view()),
    url(r'^usernames/(?P<username>\w+)/count/$', views.UserNameView.as_view()),
    url(r'^mobiles/(?P<mobile>\d+)/count/$', views.MobileView.as_view()),
    url(r'^users/$', views.UsersView.as_view()),
    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'^email/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),
    url(r'^users/(?P<user_id>\d+)/resetpassword/$', views.PasswordResetView.as_view()),
    url(r'^image_codes/(?P<image_code_id>.+)/$', views.ImageCodeView.as_view()),
    url(r'^accounts/(?P<username>\w+)/sms/token/$',views.CheckUsernameVIew.as_view()),
    url(r'^sms_codes/$',views.SendSmsCodeView.as_view()),
    url(r'^accounts/(?P<username>\w+)/password/token/$',views.CheckSmsCode.as_view()),
    url(r'^users/(?P<user_id>\d+)/password/$',views.NewPassword.as_view()),
]


