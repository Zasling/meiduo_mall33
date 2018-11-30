from django.contrib import admin
from goods import models
from celery_tasks.static_html.tasks import generate_static_list_search_html, generate_static_sku_detail_html


# SPU表的后端管理器
class GoodsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

    # 后端进行保存操作时执行
    # change修改是为true,新增为false,form里包括了原始数据与修改后的数据
    # 重写该方法是为了保存或删除时可以同时刷新静态页面
    def save_model(self, request, obj, form, change):
        # form为提交的表单数据,里面包括了所有数据,其中
        # 里面的initial里面为原始数据
        # obj为要修改的对象,每次修改要进行save()
        # request是请求对象.
        obj.save()
        generate_static_list_search_html.delay()

    def delete_model(self, request, obj):
        # 物理删除,逻辑删除的话可以obj.is_delete=Ture
        obj.delete()
        obj.save()
        generate_static_list_search_html.delay()


# SKU表后端管理器
class SKUAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_sku_detail_html.delay(obj.id)

    def delete_model(self, request, obj):
        generate_static_sku_detail_html.delay()


class SKUSpecificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()
        generate_static_sku_detail_html.delay(sku_id)


class SKUImageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_sku_detail_html.delay(obj.sku.id)

        # 设置SKU默认图片
        sku = obj.sku
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url
            sku.save()

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()
        generate_static_sku_detail_html.delay(sku_id)


# 将管理器与对应的模型类放在一起即可进行管理
admin.site.register(models.SpecificationOption)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)

admin.site.register(models.Goods, GoodsAdmin)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
admin.site.register(models.SKUImage, SKUImageAdmin)


