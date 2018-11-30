from django.db import models


class BaseModel(models.Model):
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        # 抽象类，用于继承使用，数据库迁移时不会创建BaseModel的表
        abstract = True
