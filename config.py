class Config:
    WXServerURL = "https://api.weixin.qq.com/sns/{}"
    DatabaseURL = "mysql://root:YXhxODg0OA==@localhost/wx_app"
    RedisURL = "redis://@localhost:6379/1"
    AppID = ""
    Secret = ""


class DebugConfig(Config):
    AppID = "wx41dc0f35a8d25331"
    Secret = "a15cfa3d0065911eac08fd45a8da002d"
    pass


class ProductConfig(Config):
    pass


current_config = DebugConfig()
