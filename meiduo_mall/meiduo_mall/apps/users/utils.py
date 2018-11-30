import pickle

import base64
from django.contrib.auth.backends import ModelBackend
import re
from django_redis import get_redis_connection

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'username': user.username,
        'user_id': user.id,
    }


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if re.match(r'^1[3-9]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except:
            user = None

        if user and user.check_password(password):
            return user


# 登陆合并购物车方法
def merge_cart_cookie_to_redis(request, user, response):
    # 获取cookie
    cart_cookie = request.COOKIES.get('cart_cookie', None)
    if not cart_cookie:
        return response
    cart = pickle.loads(base64.b64decode(cart_cookie))
    # 如果cookie为空,直接返回进行登陆
    if not cart:
        return response
    # 拆分数据,字典对应hash,列表对应set
    cart_dict = {}
    sku_ids = []
    sku_ids_none = []
    # 为向redis中添加数据做准备
    for sku_id, data in cart.items():
        # hash
        cart_dict[sku_id] = data['count']
        # 选中状态
        if data['selected']:
            sku_ids.append(sku_id)
        else:
            sku_ids_none.append(sku_id)
    # 建立redis链接
    conn = get_redis_connection('cart')
    # 添加多个,如果有相同数据,进行覆盖
    conn.hmset('cart_%s' % user.id, cart_dict)
    # 如果有数据
    if sku_ids:
        # 如果将列表写入集合要进行拆包
        conn.sadd('cart_selected_%s' % user.id, *sku_ids)
    if sku_ids_none:
        # 删除没选中的,不能让它登陆后添加到购物车
        conn.srem('cart_selected_%s' % user.id, *sku_ids)
    # 删除cookie
    response.delete_cookie('cart_cookie')
    return response


