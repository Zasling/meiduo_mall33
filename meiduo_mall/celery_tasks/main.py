from celery import Celery

# 为celery使用django配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建celery应用
app = Celery('meiduo')

# 导入celery配置
app.config_from_object('celery_tasks.config')

# 自动注册celery任务。它会自动注册改路径下的tasks.py文件
app.autodiscover_tasks(['celery_tasks.sms_code', 'celery_tasks.email', 'celery_tasks.static_html'])

# 启动celery应用,-A 找到任务路径，-l显示信息详情
# celery -A celery_tasks.main worker -l info
