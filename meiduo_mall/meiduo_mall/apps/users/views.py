import re

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from random import randint
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework_jwt.views import ObtainJSONWebToken
from celery_tasks.sms_code.tasks import send_sms_code
from goods.models import SKU
from goods.serializers import SKUListSerializers
from users.models import User
from users.serializers import UserSerializers, UserDetailSerializer, EmailSerializer, AddUserBrowsingHistorySerializer
from rest_framework.permissions import IsAuthenticated
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from users.utils import merge_cart_cookie_to_redis
from django.http import HttpResponse
from meiduo_mall.libs.captcha.captcha import captcha
from oauth import constants


# 发送短信
class SmsCodeView(APIView):
    def get(self, request, mobile):
        # 1.获取手机号，进行正则匹配
        conn = get_redis_connection('sms_code')
        # 先判断是否间隔了1分钟
        flag = conn.get('sms_code_flag_%s' % mobile)
        if flag:
            return Response({'error': '请求过于频繁'}, status=400)
        # 2.生成验证码
        sms_code = '%06d' % randint(0, 999999)
        print(sms_code)
        # 3. 保存验证码到redis
        pl = conn.pipeline()
        # 通过管道将2个相同操作进行整合，只需要连接一次redis
        pl.setex('sms_code_%s'%mobile, 300, sms_code)
        # 设置一个条件判断是否为1分钟后再次发送
        pl.setex('sms_code_flag_%s' %mobile, 60, 'a')
        pl.execute()
        # 4.发送验证码

        # 1.ccp = CCP()
        # 手机号， 短信验证码+过期时间，1号模板
        # ccp.send_template_sms(mobile, [sms_code, '5'], 1)
        # 2.线程
        # t = Thread(target=work, kwargs={'mobile':mobile, 'sms_code':sms_code})
        # t.start()
        # 3.celery异步发送
        send_sms_code.delay(mobile, sms_code)
        # 5.返回信息
        return Response({'message': 'ok'})

# 判断用户名
class UserNameView(APIView):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return Response({
            'username': username,
            'count': count
        })

# 判断手机号
class MobileView(APIView):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return Response({
            'mobile': mobile,
            'count': count
        })

# 绑定
class UsersView(CreateAPIView):
    serializer_class = UserSerializers

# 用户中心信息显示
class UserDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # self代表当前类实例对象(genericAPIview),使用它里面的request属性
        # 接着将数据返回给RetrieveAPIView(大部分将数据在拓展类中进行处理,在拓展类处理的过程中又用到了序列化器.)
        return self.request.user

# 发送验证邮件
class EmailView(UpdateAPIView):
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    # 原方法需要pk值,而我们的前端没有传递,所以要进行重写
    def get_object(self, *args, **kwargs):
        # 返回对象
        return self.request.user

# 验证邮箱有效性
class VerifyEmailView(APIView):
    def get(self, request):
        # 获取前端传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'error': '缺少token'}, status=400)
        tjs = TJS(settings.SECRET_KEY, 300)
        try:
            # 检查token
            data = tjs.loads(token)
        except Exception:
            return Response({'errors': '无效token'}, status=400)

        username = data['name']
        user = User.objects.get(username)
        user.email_active = True
        user.save()
        print(111)
        return Response({
            'message': 'ok'
        })

# 保存用户浏览记录
class UserBrowsingHistoryView(CreateAPIView):
    serializer_class = AddUserBrowsingHistorySerializer
    # permission_classes = [IsAuthenticated]

    # 获取用户浏览记录
    def get(self, request):
        user = request.user
        conn = get_redis_connection('history')
        # 取出5条浏览记录
        sku_ids = conn.lrange('history_%s'% user.id, 0, 6)
        # 通过sku——id在SKU表里过滤出对应的数据对象
        skus = SKU.objects.filter(id__in=sku_ids)
        # 序列化返回
        ser = SKUListSerializers(skus, many=True)

        return Response(ser.data)

# 重写ObtainJSONWebToken登陆,合并购物车
class UserAuthorizeView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            # 普通传参.传参顺序必须一致
            response = merge_cart_cookie_to_redis(request, user,response)
        # 结果返回
        return response

# 重置密码
class PasswordResetView(UpdateAPIView):

    def put(self, request,user_id):
        try:
            user = User.objects.get(id=user_id)
        except:
            return Response({'error':'数据库异常'})
        else:
            data = request.data
            # 1.获取前端密码数据
            old_password = data['old_password']
            password = data['password']
            password2 = data['password2']
            # 2.判断旧密码是否正确
            if not user.check_password(old_password):
                return Response({'error':'密码错误'})
            # 3.判断两次密码是否相同
            if password != password2:
                return Response({'error':'两次密码输入不一致'})
            # 4.旧密码正确则保存新密码
            user.set_password(password)
            user.save()
            return Response({'message': 'ok'})

# 生成图片验证码
class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self, request, image_code_id):
        name, text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection("img_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 固定返回验证码图片数据，不需要REST framework框架的Response帮助我们决定返回响应数据的格式
        # 所以此处直接使用Django原生的HttpResponse即可
        return HttpResponse(image)

# 忘记密码 - 第一步
# 检验图片验证码，判断用户名是否存在
class CheckUsernameVIew(APIView):
    def get(self,request,username):
        # 获取前端图片验证码数据
        image_code = request.GET.get('text')
        image_code_id = request.GET.get('image_code_id')
        # 验证图片验证码
        conn = get_redis_connection("img_codes")
        if not image_code:
            return Response({'error':'图片验证码错误'})
        img_code = conn.get('img_%s' % image_code_id)
        if img_code.decode().lower() != image_code.lower():
            return Response({'error':'图片验证码错误'})

        # 判断用户名是否存在
        try:
            if re.match('^1[3-9]\d{9}',username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username = username)
        except:
            return Response({'error':'用户不存在'})
        return Response({
            'mobile':user.mobile,
            'access_token':user.id,
        })

# 忘记密码-第二步
# 发送短信验证码
class SendSmsCodeView(APIView):
    def get(self, request):
        # 1.获取access_token
        access_token = request.GET.get('access_token')
        conn = get_redis_connection('sms_code')

        user = User.objects.get(id = access_token)
        mobile = user.mobile

        # 判断是否间隔了1分钟
        flag = conn.get('sms_code_flag_%s' % mobile)
        if flag:
            return Response({'error': '请求过于频繁'}, status=400)
        # 2.生成验证码
        sms_code = '%06d' % randint(0, 999999)
        print(sms_code)
        # 3. 保存验证码到redis
        pl = conn.pipeline()
        # 通过管道将2个相同操作进行整合，只需要连接一次redis
        pl.setex('sms_code_%s'% mobile, 300, sms_code)
        # 设置一个条件判断是否为1分钟后再次发送
        pl.setex('sms_code_flag_%s' % mobile, 60, 'a')
        pl.execute()
        send_sms_code.delay(mobile, sms_code)
        # 5.返回信息
        return Response({'message': 'ok'})

# 忘记密码-第三步
# 验证短信验证码
class CheckSmsCode(APIView):
    def get(self,request,username):
        # 从前端获取数据
        sms_code = request.GET.get('sms_code')
        user = User.objects.get(username = username)

        conn = get_redis_connection('sms_code')
        # 从redis中取出的数据为byte类型
        try:
            real_sms_code = conn.get('sms_code_%s' % user.mobile)
        except:
            raise Response({'message':'短信验证码过期'})
        if real_sms_code.decode().lower() != sms_code.lower():
            raise Response({'message':'验证码错误'})
        return Response({
            'user_id':user.id,
            'access_token':user.id
        })

# 忘记密码-第四步
# 保存新密码
class NewPassword(APIView):
    def post(self,request,user_id):
        pwd = request.data['password']
        pwd2 = request.data['password2']

        if pwd != pwd2:
            return Response({'message':'两次密码不一致'})
        user = User.objects.get(id = user_id)
        user.set_password(pwd)
        user.save()

        return Response('ok')
