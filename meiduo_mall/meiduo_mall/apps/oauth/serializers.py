from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from users.models import User
import re
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from django.conf import settings
from django_redis import get_redis_connection
from oauth.models import OAuthQQUser


class OauthSerializer(serializers.ModelSerializer):
    # 数据库中没有的字段要参与反序列化过程,就要显示指明,生成序列化器字段
    access_token = serializers.CharField(write_only=True)
    sms_code = serializers.CharField(write_only=True, max_length=6, min_length=6)
    token = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    # 在模型类中mobile具有唯一约束,根据它生成的序列化字段也会有这个约束,不满足需求的化就要重写这个字段
    mobile = serializers.CharField(max_length=11)

    class Meta:
        model = User
        fields = ('mobile', 'password', 'access_token', 'sms_code', 'user_id', 'token', 'username')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'max_length': 20,
                'min_length': 8
            },
            'username': {
                'read_only': True
            }

        }

    # 验证手机号
    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

    def validate(self, attrs):
        tjs = TJS(settings.SECRET_KEY, 300)
        try:
            # 如果解密成功,则openid验证通过,解密得到的类型为dict类型
            data = tjs.loads(attrs['access_token']) # {'openid':openid}
        except:
            raise serializers.ValidationError('无效的access_token')

        openid = data['openid']
        # 将取出的openid添加到attrs
        attrs['openid'] = openid

        # 验证短信验证码
        conn = get_redis_connection('sms_code')
        real_sms_code = conn.get('sms_code_%s' %attrs['mobile'])
        if not real_sms_code:
            raise serializers.ValidationError('验证码过期')

        if real_sms_code.decode() != attrs['sms_code']:
            raise serializers.ValidationError('短信验证失败')

        # 判断用户是否存在
        try:
            user = User.objects.get(mobile=attrs['mobile'])
        except:
            # 用户未注册过
            return attrs
        else:
            # 用户注册过
            # 校验密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
            return attrs

    # 上面return的attrs被此处的validated_data接收
    def create(self, validated_data):
        # 判断用户是否注册过,如果注册,直接绑定,没有则创建
        user = validated_data.get('user', None)
        if not user:
            user = User.objects.create_user(username=validated_data['mobile'], password=validated_data['password'], mobile=validated_data['mobile'])

        # 绑定openid
        OAuthQQUser.objects.create(user=user, openid=validated_data['openid'])

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token
        user.user_id = user.id
        # token与user.id都参与序列化过程,要进行返回
        return user



