import re
from rest_framework import serializers
from rest_framework.response import Response
from areas.models import Area
from users.models import Address


# 行区规划表
class AreasSerializers(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ('id', 'name')


# 收货地址信息
class AddressSerializers(serializers.ModelSerializer):
    # 前端传入的是这3个字段,序列化器要接收一下,但只让他们参与反序列化即可
    city_id = serializers.IntegerField()
    district_id = serializers.IntegerField()
    province_id = serializers.IntegerField()
    # 下面3个字段参与序列化给前端提供对应的省市区信息,如果不写.就没有这些信息返回给前端
    # 因为地区表是嵌套关联,所以可能使用primary或stringField进行指明
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Address
        # 对于user对象来说,它是前端传过来的一个token值,而token值需要用jwt进行验证而不是序列化器来验证
        exclude = ('user',)

    # 验证手机号格式
    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机格式错误')

        return value

    # 内置的方法不能保存user,需要进行重写
    # 将user添加后再继承原父类的方法
    def create(self, validated_data):
        # 在这里将用户信息一起进行保存,明确哪个用户新建的收货地址
        # context是GenericAPIView里面的方法,用来接收序列化器里的所有数据
        # 而user就在request的请求头里
        user = self.context['request'].user
        # validated_data添加用户数据
        validated_data['user'] = user
        address = super().create(validated_data)
        return address


class TitleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('title', )

    def update(self, instance, validated_data):
        # 更新操作
        if validated_data['title']:
            instance.title = validated_data['title']
        instance.save()
        return instance
