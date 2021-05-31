# Author:JZW
from rest_framework.authentication import BaseAuthentication
from api import models
from rest_framework import exceptions

class GeneralAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION',None)
        if not token:
            return None

        user_object = models.UserInfo.objects.filter(token=token).first()
        if not user_object:
            return None

        return (user_object,token)

class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION',None)
        if not token:
            raise exceptions.AuthenticationFailed()
        user_object = models.UserInfo.objects.filter(token=token).first()
        if not user_object:
            raise exceptions.AuthenticationFailed()
        return (user_object,token)
