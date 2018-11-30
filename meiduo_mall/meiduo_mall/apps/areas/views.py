import json

from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from areas.models import Area
from areas.serializers import AreasSerializers, AddressSerializers, TitleSerializer
from users.models import Address
from django.views import View


class AreasView(ListAPIView):
    """
    获取省信息
    """
    queryset = Area.objects.filter(parent=None)
    serializer_class = AreasSerializers


# 获取市与区县信息
# CacheResponseMixin
class AreaView(ListAPIView):
    # 此处parent属性是因为model里存在自关联外键
    serializer_class = AreasSerializers
    # 要获取市的信息必须先获取省的id
    # get_queryset需要一个pk值

    def get_queryset(self):
        # kwargs接收的就是字典数据,是APIView里面的方法,继承自View
        pk = self.kwargs['pk']
        # 返回Area查询集
        return Area.objects.filter(parent_id=pk)


# 展示收货地址信息与修改收货地址信息
class AddressView(CreateAPIView,UpdateAPIView,DestroyAPIView, GenericAPIView):
    serializer_class = AddressSerializers
    queryset = Address.objects.all()
    # 根据用户信息返回收货地址

    def get_queryset(self):
         return Address.objects.filter(user=self.request.user,is_deleted=False)

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response({'addresses': serializer.data})


# 修改标题与默认收货地址
class AddressStatus(UpdateAPIView):
    queryset = Address.objects.all()
    serializer_class = TitleSerializer





