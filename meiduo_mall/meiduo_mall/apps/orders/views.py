from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from goods.models import SKU
from rest_framework.generics import GenericAPIView
from decimal import Decimal
from rest_framework.generics import CreateAPIView,ListAPIView
from goods.utils import PageNum
from orders.serializers import orderInfoSerializer, CriticismSerializers
# 展示订单信息
from orders.models import OrderGoods, OrderInfo
from orders.serializers import OrderShowSerializer, OrderSaveSerializer, orderInfoSerializer


# from django.forms.models import model_to_dict
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


class CriticismView(ListAPIView):

    #　实现订单商品评论展示


    # def get(self,request,order_id):
    #
    #     try:
    #         order_id = OrderInfo.objects.filter(order_id=order_id)
    #     except:
    #         return Response('订单不存在')
    #
    #     try:
    #         skus = OrderGoods.objects.filter(order_id=order_id)
    #
    #     except:
    #         return Response('获取数据错误',status=400)
    #     # skus = model_to_dict(skus)
    #     sku_list=[]
    #     for sku in skus:
    #         data={
    #             'sku':sku.order_id,
    #             'price':sku.price,
    #             'default_image_url':sku.sku.default_image_url,
    #             'score':sku.score,
    #             'is_anonymous':sku.is_anonymous,
    #             # 'comment':sku.comment,
    #             'name':sku.sku.name,
    #             'id':sku.sku_id,
    #         }
    #         sku_list.append(data)
    #     return JsonResponse(data=sku_list,safe=False)
    serializer_class = CriticismSerializers
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        skus = OrderGoods.objects.filter(order_id=order_id)

        return skus



class SaveCriticismView(APIView):

    def post(self, request,order_id):
        # 获取前端数据
        data =request.data
        order = data['order']
        sku = data['sku.id']
        comment = data['comment']
        score = data['score']
        is_anonymous = data['is_anonymous']
        # 查询数据库
        try:
            order_id = OrderGoods.objects.filter(order_id=order_id)
        except:
            return Response({'获取数据错误'},status=400)
        # 将其覆盖














# 订单列表展示
class OrderListView(ListAPIView):
    pagination_class = PageNum
    serializer_class = orderInfoSerializer

    def get_queryset(self):
        user = self.request.user
        orders = OrderInfo.objects.filter(user_id = user.id)

        return orders



