from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from goods.models import SKU
from rest_framework.generics import GenericAPIView
from decimal import Decimal
from rest_framework.generics import CreateAPIView,ListAPIView,UpdateAPIView
from goods.utils import PageNum
from orders.serializers import orderInfoSerializer, CriticismSerializers, CriticismSaveSerializers, \
    ShowGoodsCommentSerializers
# 展示订单信息
from orders.models import OrderGoods, OrderInfo
from orders.serializers import OrderShowSerializer, OrderSaveSerializer, orderInfoSerializer


# from django.forms.models import model_to_dict
from users.models import User


class OrdersShowView(APIView):

    def get(self, request):
        # 获取用户对象
        user = request.user

        # 建立redis连接
        conn = get_redis_connection('cart')
        # 获取hash数据sku_id ,count
        sku_id_count = conn.hgetall('cart_%s' %user.id) # {10:1}
        # 将byte类型数据转为整形
        cart = {}
        for sku_id, count in sku_id_count.items():
            cart[int(sku_id)] = int(count)
        # 获取集合数据
        sku_ids = conn.smembers('cart_selected_%s' %user.id)
        # 查询所有选中状态的数据对象
        skus = SKU.objects.filter(id__in=sku_ids)
        # 商品对象添加count属性(sku表中没有count字段,要手动添加属性)
        for sku in skus:
            sku.count = cart[sku.id]
        # 生成运费
        freight = Decimal(10.00)
        # 序列化返回商品对象
        ser = OrderShowSerializer({'freight': freight, 'skus': skus})
        return Response(ser.data)


# 保存订单信息
class OrderSaveView(CreateAPIView):
    serializer_class = OrderSaveSerializer

# 订单列表展示
class OrderListView(ListAPIView):
    pagination_class = PageNum
    serializer_class = orderInfoSerializer

    def get_queryset(self):
        user = self.request.user
        orders = OrderInfo.objects.filter(user_id = user.id)

        return orders



class CriticismView(ListAPIView):
    # 展示订单中商品信息
    serializer_class = CriticismSerializers

    def get_queryset(self):
        order_id = self.kwargs['order_id']
        skus = OrderGoods.objects.filter(order_id=order_id)

        return skus


class SaveCriticismView(CreateAPIView):
    # 实现保存评论
    serializer_class = CriticismSaveSerializers

    def get_queryset(self):
        order_id = self.kwargs['order_id']
        sku = OrderGoods.objects.filter(order_id=order_id)
        return sku


class ShowGoodsCommentView(ListAPIView):
#     展示商品的评论信息
    serializer_class = ShowGoodsCommentSerializers

    def get_queryset(self):
        sku_id = self.kwargs['sku_id']
        orders = OrderGoods.objects.filter(sku_id=sku_id,is_commented=True)
        for order in orders:
            # 获取到orderinfo表中的数据
            orderinfo_id= OrderInfo.objects.get(order_id=order.order_id)
            # 获取到user对象
            user = User.objects.get(id=orderinfo_id.user_id)

            # 使商品页面展示的用户等于ｕｓｅｒ对象中的用户
            order.username = user.username
        return orders
