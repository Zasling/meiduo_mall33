from haystack import indexes
from goods.models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """
    SKU索引数据模型类
    """
    # 索引字段,document说明这个字段当做索引建立的一个来源
    # use_template表示text由哪些数据字段构成
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 会对这个模型类进行分词并建立索引
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集"""
        # 指定对于哪些数据建立索引
        return self.get_model().objects.filter(is_launched=True)






