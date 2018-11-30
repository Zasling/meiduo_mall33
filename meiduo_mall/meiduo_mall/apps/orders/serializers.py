from rest_framework import serializers
from orders.models import OrderInfo, OrderGoods
from goods.models import SKU
from django_redis import get_redis_connection
from django.db import transaction
from datetime import datetime
from decimal import Decimal
class SKUSerializer(serializers.ModelSerializer):
    # 虽然sku中有count属性,但是序列化器不定义无法提取到
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SKU
        fields = '__all__'


class OrderShowSerializer(serializers.Serializer):
    # 最大10位,最小2位小数
    freight = serializers.DecimalField(max_digits=10, decimal_places=2)
    # skus可以按照SKUSerializer所指定的内容进行返回
    skus = SKUSerializer(many=True)


class OrderSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ('address', 'pay_method', 'order_id')
        extra_kwargs = {
            'address': {
                'write_only': True,

            },
            'pay_method':{
                'write_only': True,

            },
            'order_id': {
                'read_only': True
            }
        }

    # @transaction.atomic 开启事务1
    def create(self, validated_data):
        # 获取用户
        user = self.context['request'].user
        # 生成订单标号
        order_id = datetime.now().strftime('%Y%m%d%H%M%s') +('%09d' %user.id)
        address = validated_data['address']
        pay_method = validated_data['pay_method']
        # 开启事务2
        with transaction.atomic():
            # 设置保存点
            save_point = transaction.savepoint()
            # 捕获数据库异常
            try:
                # 生成订单对象
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    pay_method=pay_method,
                    total_count=0,
                    total_amount=Decimal(0),
                    freight=Decimal(0),
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                conn = get_redis_connection('cart')
                sku_id_count = conn.hgetall("cart_%s" % user.id)
                cart_selected = conn.smembers('cart_selected_%s' % user.id)
                cart = {}
                # 构建大字典,统一数据格式
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(sku_id_count[sku_id])

                # 取出全部缓存商品
                # skus = SKU.objects.filter(id__in=cart.keys())
                # 如果使用乐观锁,则不需要先查询出全部数据
                # 处理商品
                sku_id_list = cart.keys()
                for sku_id in sku_id_list:
                    while True:
                        # 对每个遍历到的数据先进行查询
                        sku = SKU.objects.get(id=sku_id)
                        skus_count = cart[sku.id]
                        # 判断库存
                        origin_stock = sku.stock
                        # 已售出的
                        origin_sales = sku.sales

                        if origin_stock < skus_count:
                            raise serializers.ValidationError('库存不足')

                        new_stock = origin_stock - skus_count
                        new_sales = origin_sales + skus_count
                        # 对该商品进行判断,如果当前的stock=之前的stock说明没被其他用户修改,可以执行更新操作并返回1
                        ret = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,sales=new_sales)
                        if ret == 0:
                            continue
                        # 更新库存与销量
                        # sku.stock = new_stock
                        # sku.sales = new_sales
                        # sku.save()
                        # 更更新spu的总销量量
                        sku.goods.sales += skus_count
                        sku.goods.save()
                        # 更更新order商品总量量和商品总价
                        order.total_count += skus_count
                        order.total_amount += (sku.price * skus_count)
                        # 保存订单商品
                        # objects.create是在数据库中创建一条数据
                        OrderGoods.objects.create(
                            sku=sku,
                            count=skus_count,
                            order=order,
                            price=sku.price
                        )
                        # 更新成功
                        break
                # 更新订单的金额数量
                order.total_amount += order.freight
                # 最后要加一次运费,所以在for循环外面对order进行save
                order.save()
            except:
                transaction.savepoint_rollback(save_point)
            else:
                transaction.savepoint_commit(save_point)
                # 删除缓存选中状态的商品信息,选中状态在cart_selected中,对其拆包获取
                conn.hdel('cart_%s' %user.id, *cart_selected)
                conn.srem('cart_selected_%s' % user.id, *cart_selected)
                return order



