from django.core.mail import send_mail
from rest_framework import serializers

from goods.models import SKU
from users.models import User
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from celery_tasks.email.tasks import send_verify_email


# 用户绑定
class UserSerializers(serializers.ModelSerializer):
    # 显示指明那些需要接收但数据库里却没有的字段
    # 这些字段不需要序列化返回，只用在反序列化
    password2 = serializers.CharField(max_length=20,min_length=8, write_only=True)
    sms_code = serializers.CharField(max_length=6,min_length=6, write_only=True)
    allow = serializers.CharField(write_only=True)
    # 此时才能将这些字段添加到fields里
    # 只会进行序列化返回，反序列化时不会对其进行验证操作
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'mobile', 'password2', 'sms_code', 'allow', 'id', 'token')
        # 用于数据库中已经存在的字段，要添加新的额外参数
        extra_kwargs = {
            "password": {
                "write_only": True,
                "max_length": 20,
                "min_length": 8
            },
            "username": {
                "max_length": 20,
                "min_length": 5
            }
        }

    # 验证手机号格式
    def validate_mobile(self, value):
        if not re.match(r'1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机格式不匹配')
        return value

    # 验证协议状态：
    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('协议未同意')
        return value

    def validate(self, attrs):
        # 密码对比
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('密码不一致')

        conn = get_redis_connection('sms_code')
        # 从redis中取出的数据为byte类型
        real_sms_code = conn.get('sms_code_%s'%attrs['mobile'])
        if not real_sms_code:
            raise serializers.ValidationError('短信验证码过期')

        if real_sms_code.decode() != attrs['sms_code']:
            raise serializers.ValidationError('验证码错误')

        return attrs

    # 因为内置的create方法不符合我们的需求，所以在这我们进行重写
    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data['username'], password=validated_data['password'], mobile=validated_data['mobile'])

        # JWT加密
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 给user添加token属性
        user.token = token
        return user


# 用户中心信息显示
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 用户中心api返回用户信息
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


# 发送验证邮件
class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 如果使用ModelSerializer,则生成的序列化字段就自动定义好了验证email格式,不用自己定义了
        fields = ('email',)

        extra_kwargs = {
            'email': {
                'required': True
            },
        }

    def update(self, instance, validated_data):
        # 更新操作
        instance.email = validated_data['email']
        instance.save()
        # 发送邮件
        # subject, message, from_email, recipient_list,html_message=None
        # message为普通正文,有转义. html_message为html字符串
        data = {'name': instance.username}
        tjs = TJS(settings.SECRET_KEY, 300)
        token = tjs.dumps(data).decode()
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token
        # send_mail(subject, '', settings.EMAIL_FROM, [validated_data['email']], html_message=html_message)
        send_verify_email.delay(validated_data['email'], verify_url)

        return instance


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览历史序列化器
    """
    # sku_id与模型类没有关系,所以使用Serializer
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    # def validate_sku_id(self, value):
    #     try:
    #         SKU.objects.get(id=value)
    #     except SKU.DoesNotExist:
    #         raise serializers.ValidationError('该商品不存在')
    #     return value

    def validate(self, attrs):
        # 判断sku——id对应的商品是否存在
        try:
            SKU.objects.get(id=attrs['sku_id'])
        except:
            raise serializers.ValidationError('商品不存在')
        return attrs

    def create(self, validated_data):
        # 建立redis连接
        conn = get_redis_connection('history')
        # request可以提取请求对象
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        pl = conn.pipeline()
        # 移除已经存在的商品数据
        # lrem:key.当中间参数>0时,从左删除第一个,=0全删,<0从右删第一个,参数3为删除条件
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 添加新的商品数据
        pl.lpush("history_%s" % user_id, sku_id)
        # 只保存最多5条记录
        pl.ltrim("history_%s" % user_id, 0, 4)
        pl.execute()

        return validated_data





