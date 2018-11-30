from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^areas/$', views.AreasView.as_view()),
    # 如果路由匹配成功,会生成一个字典数据{'pk':1300}
    url(r'^areas/(?P<pk>\d+)/$', views.AreaView.as_view()),
    url(r'^addresses/$', views.AddressView.as_view()),
    url(r'^addresses/(?P<pk>\d+)/$', views.AddressView.as_view()),
    url(r'^addresses/(?P<pk>\d+)/status/$', views.AddressStatus.as_view()),
    url(r'^addresses/(?P<pk>\d+)/title/$', views.AddressStatus.as_view()),

]
