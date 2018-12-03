from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from oauth.models import OAuthQQUser, OAuthSinaUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from oauth.serializers import OauthSerializer
from oauth.wbtool import OAuthWB
from users.models import User
from users.utils import merge_cart_cookie_to_redis
from meiduo_mall.libs.captcha import captcha
from oauth import constants
# 图片验证码
class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self, request, image_code_id):
        # 生成验证码图片
        name, text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 固定返回验证码图片数据，不需要REST framework框架的Response帮助我们决定返回响应数据的格式
        # 所以此处直接使用Django原生的HttpResponse即可
        return HttpResponse(image)

# 构建qq登陆的跳转链接
class OauthLoginView(APIView):
    # 获取前端state
    def get(self, request):
        # 1.获取前端传递的state,key值为next
        state = request.query_params.get('next', None)
        # 2.判断state是否存在,没有则手动创建
        if not state:
            state = '/'
        # 3.初始化OAuthQQ对象
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET, redirect_uri=settings.QQ_REDIRECT_URI, state=state)
        # 4.构造qq跳转链接
        login_url = qq.get_qq_url()
        # 5.返回结果
        return Response({'login_url': login_url})


class OauthView(CreateAPIView):
    # 只继承CreateAPIView的话只需要serializer_class即可
    # 当执行绑定openid时(post请求),执行序列化器里的方法
    serializer_class = OauthSerializer

    # 获取openid
    def get(self, request):
        # 1.获取code值
        # 2.判断前端是否传递code值
        # 3.通过code值获取access_token值,需先建立qq对象
        # 4.通过access_token获取openid值
        code = request.GET.get('code', None)
        if not code:
            return Response({'error': '　缺少code值'})
        state = '/'
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI, state=state)

        try:
            access_token = qq.get_access_token(code)
            openid = qq.get_open_id(access_token)
        except Exception:
            return Response({'message': 'QQ服务异常'}, status=503)

        # 判断openid是否绑定
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except Exception:
            # 捕获到异常说明openid不存在,用户没有绑定过,将openid返回,用于绑定用户身份并进入绑定界面
            tjs = TJS(settings.SECRET_KEY, 300)
            # 加密之后为byte类型,要先解码
            open_id = tjs.dumps({'openid': openid}).decode()
            return Response({'access_token': open_id})
        else:
            user = oauth_user.user
            # 存在则用户登陆成功,跳转到首页,绑定token值
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id,
            })
            merge_cart_cookie_to_redis(request, user, response)
            return response

# 构建微博跳转链接
class OauthWeiboLoginView(APIView):
    # 获取前端state
    def get(self, request):
        # 1.获取前端传递的state,key值为next
        state = request.query_params.get('next', None)
        # 2.判断state是否存在,没有则手动创建
        if not state:
            state = '/'
        # 3.初始化OAuthWeibo对象
        weibo = OAuthWB(client_id=settings.WEIBO_APP_ID, client_secret=settings.WEIBO_APP_KEY, redirect_uri=settings.WEIBO_REDIRECT_URI, state=state)
        # 4.构造qq跳转链接
        login_url = weibo.get_weibo_url()
        # 5.返回结果
        return Response({'login_url': login_url})

# 判断用户是否绑定
class WbOauthView(CreateAPIView):
    serializer_class = OauthWeiboLoginView

    # 获取access_token
    def get(self, request):
        # 1.获取code值
        code = request.GET.get('code', None)
        # 2.判断前端是否传递code值
        if not code:
            return Response({'error': '　缺少code值'})
        # 3.通过code值获取access_token值,需先建立weibo对象
        state = '/'
        weibo = OAuthWB(client_id=settings.WEIBO_APP_ID, client_secret=settings.WEIBO_APP_KEY, redirect_uri=settings.WEIBO_REDIRECT_URI, state=state)
        try:
            access_token = weibo.get_access_token(code)
        except Exception:
            return Response({'message': '微博服务异常'}, status=503)

        # 4.判断access_token否绑定
        try:
            oauth_user = OAuthSinaUser.objects.get(access_token=access_token)
        except Exception:
            # 捕获到异常说明access_token不存在,用户没有绑定过,将access_token返回,用于绑定用户身份并进入绑定界面
            tjs = TJS(settings.SECRET_KEY, 300)
            # 加密之后为byte类型,要先解码
            accesstoken = tjs.dumps({'access_token': access_token}).decode()
            return Response({'access_token': accesstoken})
        else:
            # 存在则用户登陆成功,跳转到首页,绑定token值
            user = oauth_user.user

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id,
            })
            merge_cart_cookie_to_redis(request, user, response)
            return response




