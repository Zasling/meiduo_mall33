from drf_haystack.viewsets import HaystackViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from goods.models import GoodsCategory
from rest_framework.generics import ListAPIView
from goods.models import SKU
from rest_framework.filters import OrderingFilter
from goods.serializers import SKUListSerializers, SKUSearchSerializers
from goods.utils import PageNum


# 面包屑导航分类获取
class CategoriesView(APIView):
    def get(self, request, pk):
        # 查询3级分类
        # 下面的parent与name都是表里面的字段属性
        cat3 = GoodsCategory.objects.get(id=pk)
        cat2 = cat3.parent
        cat1 = cat2.parent

        return Response({
            'cat1': cat1.name,
            'cat2': cat2.name,
            'cat3': cat3.name,
        })


class SkuListView(ListAPIView):
    # 获取当前分类下的所有商品详情数据
    # 当原有的queryset不能接收pk参数
    def get_queryset(self):
        pk = self.kwargs['pk']
        return SKU.objects.filter(category_id=pk)

    serializer_class = SKUListSerializers

    pagination_class = PageNum

    filter_backends = [OrderingFilter]
    ordering_fields = ('sales', 'price', 'create_time')


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    # 检索出符合条件数据的id值
    # 再根据检索出来的id值取查询SKU表对应的数据
    index_models = [SKU]
    # 指定序列化器,将检索出来的数据进行序列化返回
    serializer_class = SKUSearchSerializers
    pagination_class = PageNum



