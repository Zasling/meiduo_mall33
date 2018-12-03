from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/settlement/$', views.OrdersShowView.as_view()),
    url(r'^orders/$', views.OrderSaveView.as_view()),
    url(r'^ordersList/$', views.OrderListView.as_view()),
    url(r'^orders/(?P<order_id>\d+)/uncommentgoods/$', views.OrderComment.as_view()),
    url(r'^orders/(?P<order_id>\d+)/comments/$', views.SaveSkuComment.as_view()),
    url(r'^skus/(?P<sku_id>\d+)/comments/$', views.ShowComment.as_view()),

]