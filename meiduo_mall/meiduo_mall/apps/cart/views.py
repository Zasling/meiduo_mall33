import pickle

import base64
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken
from goods.models import SKU
from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from django_redis import get_redis_connection


class CartView(APIView):
    """
    购物车
    """
    # 进入视图之前会执行initial方法,该方法内部就有检查jwt的方法
    def perform_authentication(self, request):
        """
        重写父类的用户验证方法，不在进入视图前就检查JWT
        """
        pass

    def post(self, request):
        """
       添加购物车
       """
        data = request.data
        ser = CartSerializer(data=data)
        ser.is_valid()

        sku_id = ser.validated_data['sku_id']
        count = ser.validated_data['count']
        selected = ser.validated_data['selected']
        # 尝试对请求用户进行验证
        try:
            user = request.user
        except Exception:
            # 获取不到说明用户没有登陆
            user = None
        if user:
            # 连接redis
            conn = get_redis_connection('cart')
            # 保存hash,sku_id和count
            # 如果有用户,则添加时为+1操作
            conn.hincrby('cart_%s' %user.id, sku_id, count)
            # 如果为选中状态,写入到集合中
            if selected:
                conn.sadd('cart_selected_%s' %user.id, sku_id)
            return Response({'count': count})
        # 未登录
        else:
            # 生成响应对象
            response = Response({'count': count})
            # 尝试获取cookie,判断以前是否登陆过
            # {10:{count:1, 'selected':true}}
            cart_cookie = request.COOKIES.get('cart_cookie' , None)
            if cart_cookie:
                # 存储过,则解密cookie
                cart = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart = {}
            # 根据sku_id取出小字典,如果能取到，说明以前添加过
            # 对count进行累加
            sku = cart.get(sku_id)
            if sku:
                # 如果商品存在,写入新数据
                count += int(sku['count'])
            cart[sku_id] = {
                'count':count,
                'selected': selected
            }
            # 加密字典数据
            # decode将byte类型解密为字符串类型
            cart_cookie = base64.b64encode(pickle.dumps(cart)).decode()
            # 写入cookie
            response.set_cookie('cart_cookie', cart_cookie, 60*60*24)
            return response

    def get(self, request):
        # 获取只需要一个token
        try:
            user = request.user
        except Exception:
            # 获取不到说明用户没有登陆
            user = None
        if user:
            # 连接redis
            conn = get_redis_connection('cart')
            # 获取hash,sku_id和count
            sku_id_count = conn.hgetall('cart_%s' %user.id)# {sku_id: count}
            # 获取选中状态,sets
            sku_ids = conn.smembers('cart_selected_%s' %user.id)# {sku_id1:sku_id2}
            # 数据格式统一,{10:{count:10,selected:true}}
            cart = {}
            for sku_id, count in sku_id_count.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in sku_ids
                }
        # 未登录
        else:
            # 尝试获取cookie,判断以前是否登陆过
            # {10:{count:1, 'selected':true}}
            cart_cookie = request.COOKIES.get('cart_cookie' , None)
            if cart_cookie:
                # 存储过,则解密cookie
                cart = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart = {}

        # 获取字典中的sku_id.Dict.keys()
        sku_id_list = cart.keys()
        # id__in根据返回查询
        skus = SKU.objects.filter(id__in=sku_id_list)
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']
        ser = CartSKUSerializer(skus, many=True)
        return Response(ser.data)

    def put(self, request):
        data = request.data
        ser = CartSerializer(data=data)
        ser.is_valid()

        sku_id = ser.validated_data['sku_id']
        count = ser.validated_data['count']
        selected = ser.validated_data['selected']
        try:
            user = request.user
        except Exception:
            # 获取不到说明用户没有登陆
            user = None
        if user:
            # 连接redis
            conn = get_redis_connection('cart')
            conn.hset('cart_%s' % user.id, sku_id, count)  # {sku_id: count}
            if selected:
                conn.sadd('cart_selected_%s' %user.id, sku_id)
            else:
                conn.srem('cart_selected_%s' %user.id, sku_id)
            return Response(ser.data)
        # 未登录
        else:
            cart_cookie = request.COOKIES.get('cart_cookie', None)
            if cart_cookie:
                # 存储过,则解密cookie
                cart = pickle.loads(base64.b64decode(cart_cookie))
            else:
                cart = {}
            # 获取字典中的sku_id.Dict.keys()
            cart[sku_id] = {
                'count': count,
                'selected': selected
            }
            response = Response(ser.data)
            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
            # 给相应对象写入cookie为固定写法
            # 当请求这个视图时,自动加上这个cookie
            response.set_cookie('cart', cookie_cart, max_age=60*60*24)
            return response

    def delete(self, request):
        """
       添加购物车
       """
        data = request.data
        ser = CartDeleteSerializer(data=data)
        ser.is_valid()
        sku_id = ser.validated_data['sku_id']
        # 尝试对请求用户进行验证
        try:
            user = request.user
        except Exception:
            # 获取不到说明用户没有登陆
            user = None
        if user:
            # 连接redis
            conn = get_redis_connection('cart')
            conn.hdel('cart_%s' %user.id, sku_id)
            # 如果为选中状态,写入到集合中
            conn.srem('cart_selected_%s' % user.id, sku_id)
            return Response({'message': 'ok'})
        # 未登录
        else:
            # 生成响应对象
            response = Response({'message': 'ok'})
            # 尝试获取cookie,判断以前是否登陆过
            # {10:{count:1, 'selected':true}}
            cart_cookie = request.COOKIES.get('cart_cookie', None)
            if cart_cookie:
                # 解密的时候可以不是byte类型
                cart = pickle.loads(base64.b64decode(cart_cookie))
                # 如果商品在购物车里
                if sku_id in cart.keys():
                    del cart[sku_id]
                    cart_cookie = base64.b64encode(pickle.dumps(cart)).decode()
                    # 写入cookie
                    response.set_cookie('cart_cookie', cart_cookie, 60*60*24)
            return response


# 购物车全选操作
class CartsSelectionView(APIView):
    def perform_authentication(self, request):
        pass

    def put(self, request):
        data = request.data
        ser = CartSelectAllSerializer(data=data)
        ser.is_valid()
        selected = ser.validated_data['selected']
        try:
            user = request.user
        except Exception:
            # 获取不到说明用户没有登陆
            user = None
        if user:
            # 连接redis
            conn = get_redis_connection('cart')
            # 获取hash,sku_id和count
            sku_id_count = conn.hgetall('cart_%s' % user.id)  # {sku_id: count}
            # sku_ids为列表
            sku_ids = sku_id_count.keys()
            if selected:
                # 写入set要先对列表进行拆包
                conn.sadd('cart_selected_%s' %user.id, *sku_ids)
            else:
                conn.srem('cart_selected_%s' %user.id, *sku_ids)
            return Response({'message': 'OK'})
        # 未登录
        else:
            response = Response({'message': 'OK'})
            cart_cookie = request.COOKIES.get('cart_cookie', None)
            if cart_cookie:
                # 存储过,则解密cookie
                cart = pickle.loads(base64.b64decode(cart_cookie))
                for sku_id, data in cart.items():
                    data['selected'] = selected

                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                # 给相应对象写入cookie为固定写法
                # 当请求这个视图时,自动加上这个cookie
                response.set_cookie('cart', cookie_cart, max_age=60*60*24)
            return response


