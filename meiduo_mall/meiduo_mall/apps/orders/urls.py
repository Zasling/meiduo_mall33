from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/settlement/$', views.OrdersShowView.as_view()),
    url(r'^orders/$', views.OrderSaveView.as_view()),
    url(r'^ordersList/$', views.OrderListView.as_view()),

]