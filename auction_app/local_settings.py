# Author:JZW
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api.apps.ApiConfig',
    'rest_framework',
]

#Redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.10:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "PASSWORD": "jzw15840665319",
        }
    }
}

#MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '192.168.40.10',  # 数据库主机
        'PORT': 3306,  # 数据库端口
        'USER': 'root',  # 数据库用户名
        'PASSWORD': 'jzw15840665319',  # 数据库用户密码
        'NAME': 'Auction'  # 数据库名字
    }
}

#Tencent Message
TENCENT_SECRET_ID = "AKID5A1MHyit1sMpnXw53kqx7LKXXpsqjAej"
TENCENT_SECRET_KEY = "kPvCHBsYDQOeQW5UvFFKEqFXjU3WuDH7"
TENCENT_CITY = "ap-beijing"
TENCENT_APP_ID = "1400465260"
TENCENT_SIGN = "CodeChaser"