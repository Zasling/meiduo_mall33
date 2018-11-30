from django.conf.urls import url
from . import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^categories/(?P<pk>\d+)/$', views.CategoriesView.as_view()),
    url(r'^categories/(?P<pk>\d+)/skus/$', views.SkuListView.as_view()),

]
router = DefaultRouter()
router.register('skus/search',views.SKUSearchViewSet, base_name='skus_search')
# 将生成的路由添加到urlpatterns
urlpatterns += router.urls

