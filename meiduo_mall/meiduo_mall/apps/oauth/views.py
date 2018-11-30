from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from oauth.models import OAuthQQUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from oauth.serializers import OauthSerializer
from users.models import User
# 第三方登陆管理视图


# 构建qq登陆的跳转链接
from users.utils import merge_cart_cookie_to_redis


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



