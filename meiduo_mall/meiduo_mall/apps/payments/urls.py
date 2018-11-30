from django.conf.urls import url
from django.contrib import admin
from . import views
urlpatterns = [
    url(r'^orders/(?P<order_id>\w+)/payment/$', views.PaymentURLView.as_view()),
    url(r'^payment/status/$', views.PaymentView.as_view()),
]

