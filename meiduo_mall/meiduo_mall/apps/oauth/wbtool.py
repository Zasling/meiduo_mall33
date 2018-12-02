import re

from django.conf import settings
from urllib.parse import urlencode, parse_qs
import json
import requests
from svgwrite import params


class OAuthWB(object):
    """
    wb认证辅助工具类
    """

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state   # 用于保存登录成功后的跳转页面路径

    def get_wb_url(self):
        # QQ登录url参数组建
        data_dict = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state
        }

        # 构建url
        wb_url = 'https://api.weibo.com/oauth2/authorize?client_id=' + settings.WEIBO_APP_ID + '&redirect_uri=' + settings.WEIBO_REDIRECT_URI
        # qq_url = 'https://api.weibo.com/oauth2/authorize?' + urlencode(data_dict)

        return wb_url

    # 获取access_token值


    def get_access_token(self, code):
        # 构建参数数据
        data_dict = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code,
        }

        # 构建url
        access_url = 'https://api.weibo.com/oauth2/access_token'

        # 发送请求,请求中要携带５个参数为data_dict
        try:
            response = requests.post(access_url,data=data_dict)

            # 提取数据
            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
            data = response.text
            # print(type(data))
            # date = re.sub("\"",'',data)

            # 转化为字典
            data = json.loads(data)
            # print(data)
        except:
            raise Exception('qq请求失败')

        # 提取access_token
        access_token = data.get('access_token', None)


        if not access_token:
            raise Exception('access_token获取失败')

        return access_token

