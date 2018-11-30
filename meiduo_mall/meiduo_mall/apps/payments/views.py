import os
from alipay import AliPay
from django.conf import settings
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import OrderInfo


# Create your views here.
from payments.models import Payment


class PaymentURLView(APIView):
    """
        构建跳转连接
    """

    def get(self, request, order_id):
        # 1、获取订单编号
        # 2、验证当前订单
        try:
            order = OrderInfo.objects.get(order_id=order_id, pay_method=2, status=1)
        except:
            return Response({'error': '订单错误'}, status=405)
        # 3、生成支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # 4、生成跳转链接
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单编号
            total_amount=str(order.total_amount),
            subject='美多商城%s' % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
        )
        alipay_url = settings.ALIPAY_URL + order_string
        # 5、结果返回
        return Response({'alipay_url': alipay_url})


class PaymentView(APIView):

    """
        保存支付结果
    """

    def put(self,request):
        # 1、获取数据

        data=request.query_params.dict()
        # sign 不能参与签名验证
        signature = data.pop("sign")
        # 2、验证数据
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        success = alipay.verify(data, signature)

        if success:
            order_id=data['out_trade_no']
            trade_id=data['trade_no']
            # 3、保存数据
            Payment.objects.create(order_id=order_id,trade_id=trade_id)
            # 更新订单状态
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            # 4、返回结果
            return Response({'trade_id': trade_id})
        else:
            return Response({'error':'验证失败'},status=400)


