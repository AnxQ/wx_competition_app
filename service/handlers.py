import json

import requests
import tornado.web

from service.db import User, Comp, CompStatus
from service.redis import new_login_session, get_login_openid
from service.utils import WeChat


class Result:
    @staticmethod
    def Success():
        return json.dumps({"result": "success"})

    @staticmethod
    def Failed(code):
        return json.dumps({"result": "failed",
                           "reason": code})

    @staticmethod
    def Redirect(route):
        return json.dumps({"result": "redirect",
                           "router": route})


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
        self.write(Comp.get_comp(1))

    def post(self):
        pass

    def put(self):
        comp = Comp(status=CompStatus.open)
        comp.new_comp()
        self.set_status(204)


class AuthHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            # Already logged && session still alive
            self.set_status(204)
            return
        user_info = WeChat.get_user_info(js_code=self.request.arguments['code'][0].decode())
        user_uuid = new_login_session(openid=user_info['openid'], session_key=user_info['session_key'])
        self.set_header('Authorization', user_uuid)
        print(f"Login: {user_uuid} {user_info['openid']}")
        if User.get_user(user_info['openid']):
            pass
        else:
            User.new_user(user_info['openid'])
            self.write(Result.Redirect(""))
        self.set_status(200)


class UserHandler(BaseHandler):
    @authenticated
    def get(self):
        user: User = self.current_user
        self.write(json.dumps(user.info_dict))

    @authenticated
    def post(self):
        user: User = self.current_user
        try:
            update_data = json.loads(self.request.body)
            user.update_user_info(update_data)
            self.set_status(200)
            self.write(Result.Success())
        except Exception:
            self.set_status(400)
            self.write(Result.Failed(400))


class CompetitionsHandler(BaseHandler):
    def get(self):
        args = self.request.arguments
        filters = json.loads(self.request.body) if self.request.body else None
        tags = args['tags'] if 'tags' in args else []

        def date_filter():
            return lambda: filters['date_to'] > Comp.time_begin > filters['date_from']

        require_page = args['page'][0].decode() if 'page' in args else 0
        self.write(json.dumps(Comp.get_comps(comp_filters=[], tags=tags, page=require_page)))


class CompetitionHandler(BaseHandler):
    def get(self):
        args = self.request.arguments
        if "id" in args:
            res = Comp.get_comp(comp_id=args["id"])
            self.write(json.dumps(res))
            self.set_status(200)
        else:
            self.write(Result.Failed("Argument Illegal."))
            self.set_status(400)

    def put(self):
        pass

    def post(self):
        pass


class ProxyHandler(BaseHandler):
    def get(self):
        link = self.request.arguments['link'][0].decode()
        res = requests.get(link)
        self.write(res.content)
