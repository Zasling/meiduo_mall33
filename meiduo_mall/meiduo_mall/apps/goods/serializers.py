from rest_framework import serializers
from goods.models import SKU
from drf_haystack.serializers import HaystackSerializer

from goods.search_indexes import SKUIndex


# 显示所有当前商品的所有数据
class SKUListSerializers(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = '__all__'


class SKUSearchSerializers(HaystackSerializer):
    # 将数据对象在进行返回时,按嵌套序列化器的方式进行返回
    object = SKUListSerializers()

    class Meta:
        # 指定索引类,进行序列化返回时,可以将里面的索引字段返回
        index_classes = [SKUIndex]
        fields = ('text', 'object')

