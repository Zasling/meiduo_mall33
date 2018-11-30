from rest_framework import serializers
from goods.models import SKU


# 增加,修改
class CartSerializer(serializers.Serializer):
    """
    购物车数据序列化器
    """
    # 1.获取参数
    sku_id = serializers.IntegerField(label='sku id ', min_value=1)
    count = serializers.IntegerField(label='数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    # 2.验证参数

    def validate(self, attrs):
        try:
            sku = SKU.objects.get(id=attrs['sku_id'])

        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        if attrs['count'] > sku.stock:
            raise serializers.ValidationError('商品库存不足')
        return attrs


# 获取购物车商品
class CartSKUSerializer(serializers.ModelSerializer):
        """
       购物车商品数据序列化器
       """
        # 1.要返回商品数据对象,所有要用ModelSerializer
        # 2.如果不写read_only=True,则会报SKU没有这2个属性的错误,因为默认是这2个属性参数序列化与反序列化,但模型类中并没有这2个属性.
        count = serializers.IntegerField(label='数量', read_only=True)
        selected = serializers.BooleanField(label='是否勾选', read_only=True)

        class Meta:
            model = SKU
            fields = ('id', 'count', 'name', 'default_image_url', 'price','selected')


class CartDeleteSerializer(serializers.Serializer):
    """
    删除购物车数据序列化器
    """
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate(self, attrs):
        try:
            SKU.objects.get(id=attrs['sku_id'])
        except SKU.DoesNotExist:
            serializers.ValidationError('商品不存在')

        return attrs


class CartSelectAllSerializer(serializers.Serializer):
    """
    购物车全选
    """
    selected = serializers.BooleanField(default=True)


