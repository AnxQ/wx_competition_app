import requests
from config import current_config


class WeChat:
    @staticmethod
    def get_user_info(js_code):
        req_params = {"appid": current_config.AppID,
                      "secret": current_config.Secret,
                      "js_code": js_code,
                      "grant_type": 'authorization_code'}
        req_result = requests.get(current_config.WXServerURL.format("jscode2session"),
                                  params=req_params, timeout=3, verify=False)
        return req_result.json()
