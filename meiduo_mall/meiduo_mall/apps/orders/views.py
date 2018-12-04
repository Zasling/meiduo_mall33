from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
from rest_framework.generics import CreateAPIView,ListAPIView
from rest_framework.mixins import ListModelMixin
from orders.serializers import OrderShowSerializer, OrderSaveSerializer, OrderListSerializer, CommentSerializers, \
    CommentSaveSerializers, CommentShowSerializers
from users.models import User
from orders.models import OrderInfo,OrderGoods
from orders.utils import PageNum
from rest_framework.filters import OrderingFilter

# 展示订单信息
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
class OrderSaveView(ListModelMixin, CreateAPIView):
    serializer_class = OrderSaveSerializer

# 订单列表数据获取
class OrderListView(ListAPIView):
    pagination_class = PageNum

    serializer_class = OrderListSerializer

    def get_queryset(self):
        user = self.request.user
        order = OrderInfo.objects.filter(user = user)
        return order


# 评论-获取商品信息
class OrderComment(ListAPIView):
    serializer_class = CommentSerializers
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        skus = OrderGoods.objects.filter(order_id = order_id, is_commented=False)
        return skus

# 保存评论
class SaveSkuComment(CreateAPIView):
    serializer_class = CommentSaveSerializers

# 商品详情中的评论展示
class ShowComment(ListAPIView):
    serializer_class = CommentShowSerializers
    def get_queryset(self):
        # 从kwargs中获取sku_id
        sku_id = self.kwargs['sku_id']
        # 获取商品信息
        orders = OrderGoods.objects.filter(sku_id=sku_id, is_commented = True)
        for sku in orders:
            skuinfo = OrderInfo.objects.get(order_id=sku.order_id)
            user = User.objects.get(id = skuinfo.user_id)
            # 获取用户名，判断是否匿名
            sku.username = user.username
            if sku.is_anonymous == True:
                sku.username = '****'
        return orders



