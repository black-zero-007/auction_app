# Author:JZW
import uuid
import hashlib
import time

from django.conf import settings

def md5(string):
    ha = hashlib.md5()
    ha.update(string.encode('utf-8'))
    return ha.hexdigest()

def create_id(nickname):
    string = '{}-{}-{}'.format(nickname,time.time(),uuid.uuid4())
    md5_object = hashlib.md5(settings.TENCENT_SECRET_KEY.encode('utf-8'))
    md5_object.update(string.encode('utf-8'))
    return md5_object.hexdigest()