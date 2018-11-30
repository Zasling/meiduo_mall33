from meiduo_mall.libs.yuntongxun.sms import CCP
# 将main里面的注册好的app导入
from celery_tasks.main import app


# 添加任务名
@app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    ccp = CCP()
    ccp.send_template_sms(mobile, [sms_code, '5'], 1)

