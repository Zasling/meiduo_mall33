from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.utils.deconstruct import deconstructible


@deconstructible
# 此处的类名在dev中已经被规定好
class FastDFSStorage(Storage):
    def __init__(self, base_url=None, client_conf=None):
        """
        初始化
        :param base_url: 用于构造图片完整路径使用，图片服务器的域名
        :param client_conf: FastDFS客户端配置文件的路径
        """
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            # client_conf,Fast配置路径
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def _open(self, name, mode='rb'):
        # 不让django执行打开文件操作
        pass

    def _save(self, name, content):
        # 连接fastdfs / 连接七牛云
        client = Fdfs_client(self.client_conf)
        # 文件上传,并返回dict类型的上传结果信息
        # 此处上传成功后,会返回一个结果对象
        ret = client.upload_by_buffer(content.read())
        # 判断返回结果
        if ret['Status'] != 'Upload successed.':
            raise Exception('upload file failed')
        # 在返回对象中获取file_id
        file_id = ret['Remote file_id']
        # 返回file_id
        return file_id

    def url(self, name):
        # 拼接完整路径,name就是上面的file_id
        return self.base_url + name

    def exists(self, name):
        # 不让django判断是否重复
        return False



