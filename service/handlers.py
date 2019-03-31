import json

import tornado.web

from service.db import User
from service.redis import new_login_session, get_login_openid
from service.utils import WeChat


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self) -> User:
        openid = None
        if 'Authorization' in self.request.headers:
            openid = get_login_openid(self.request.headers['Authorization'])
        return None if openid is None else User.get_user(openid)


# Tencent framework is piece of shit so that maintenance a session myself
def authenticated(func):
    def inner(self, *args, **kwargs):
        if self.current_user:
            print(f"Access: {self.current_user.open_id}")
            func(self, *args, **kwargs)
        else:
            self.set_status(403)
            self.write("Illegal access")

    return inner


class TestHandler(BaseHandler):
    def get(self):
        self.write(self.current_user)
        self.write("Hello, world")

    def post(self):
        print(self.request.remote_ip)
        print(self.request.body.decode())
        print(self.request.arguments)
        print(self.request.query_arguments)
        print(self.request.headers['Host'])


class AuthHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            # Already logged && session still alive
            self.set_status(204)
            return
        req_data = json.loads(self.request.arguments)
        user_info = WeChat.get_user_info(js_code=req_data['js_code'])
        user_uuid = new_login_session(openid=user_info['openid'], session_key=user_info['session_key'])
        self.set_header('Authorization', user_uuid)
        print(f"Login: {user_uuid} {user_info['openid']}")
        if User.get_user(user_info['openid']):
            pass
        else:
            User.new_user(user_info['openid'])

        self.set_status(204)


class UserHandler(BaseHandler):
    @authenticated
    def get(self):
        user: User = self.current_user
        self.write(json.dumps(user.get_user_info()))

    @authenticated
    def put(self):
        user: User = self.current_user
        req_data = json.loads(self.request.body)
        User.update_user_info(

        )



class CompetitionHandler(BaseHandler):
    def get(self):
        pass
