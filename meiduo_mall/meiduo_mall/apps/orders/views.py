from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
from rest_framework.generics import CreateAPIView

# 展示订单信息
from orders.serializers import OrderShowSerializer, OrderSaveSerializer


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



