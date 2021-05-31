import random
import uuid
import json
import requests

from api import serializer,models

from until.entcrypt import create_id
from until.tencent.msg import send_china_msg
from until.pagination import MiniLimitOffsetPagination
from until.authentication import GeneralAuthentication,UserAuthentication
from until.filters import MaxFilterBackend,MinFilterBackend,CollectMaxFilterBackend,CollectMinFilterBackend,NewsMaxFilterBackend,NewsMinFilterBackend

from django.shortcuts import render
from django.db.models import F
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView,CreateAPIView,RetrieveAPIView

# Create your views here.
class MessagesView(APIView):
    def get(self,request,*args,**kwargs):
        """
        发送手机验证码
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        #1.获取手机号
        #2.手机格式校验
        ser = serializer.MessageSerializer(data=request.query_params)
        if not ser.is_valid():
            return Response({'status':False,'message':'手机号格式错误'})
        phone = ser.validated_data.get('phone')
        #3.生成随机验证码
        random_code = random.randint(100000,999999)
        result = send_china_msg(phone,random_code)
        print(result.message)
        if not result:
            return Response({'status':False,'message':'短信发送失败'})
        print(random_code)
        conn = get_redis_connection()
        conn.set(phone,random_code,ex=60)
        return Response({'status':True,'message':'短信发送成功'})

class LoginView(APIView):
    def post(self,request,*args,**kwargs):
        # print(request.data)
        ser = serializer.LoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'status':False,'messages':'验证码错误','detail':ser.errors})
        wx_code = ser.validated_data.get('wx_code')
        # print(wx_code)
        params = {
            'appid':'wx359505d7e4f9e776',
            'secret':'54498f27474ecd4a72ca6988a7dd096d',
            'js_code':wx_code,
            'grant_type':'authorization_code'
        }
        result_dict = requests.get('https://api.weixin.qq.com/sns/jscode2session',params=params).json()
        # print(result_dict)
        phone = ser.validated_data.get('phone')
        token = create_id(phone)
        nickname = json.dumps(request.data.get('nickname'))
        user_object = models.UserInfo.objects.filter(phone=phone).first()
        if not user_object:
            models.UserInfo.objects.create(
                **result_dict,
                token=token,
                phone=phone,
                nickname=nickname,
                avatar=request.data.get('avatar')
            )
        else:
            models.UserInfo.objects.filter(phone=phone).update(
                **result_dict,
                token=token,
                phone=phone,
                nickname=nickname,
                avatar=request.data.get('avatar')
            )
        return Response({'status':True,'data':{'token':token,'phone':phone}})

class HomeView(APIView):
    def get(self,request,*args,**kwargs):
        token = request.query_params.get('token')
        user_object = models.UserInfo.objects.filter(token=token).first()
        ser = serializer.HomeModelSerializer(instance=user_object)
        return Response(ser.data,status=status.HTTP_200_OK)

class CredentialTwoView(APIView):
    def get(self,request,*args,**kwargs):
        from sts.sts import Sts
        from django.conf import settings
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            'domain': 'sts.tencentcloudapi.com',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 1800,
            'secret_id': settings.TENCENT_SECRET_ID,
            # 固定密钥
            'secret_key': settings.TENCENT_SECRET_KEY,
            # 设置网络代理
            # 'proxy': {
            #     'http': 'xx',
            #     'https': 'xx'
            # },
            # 换成你的 bucket
            'bucket': 'auction-1304610462',
            # 换成 bucket 所在地区
            'region': 'ap-nanjing',
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': '*',
            # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
            'allow_actions': [
                # 简单上传
                'name/cos:PostObject',
                'name/cos:DeleteObject',
            ],
        }

        try:
            sts = Sts(config)
            response = sts.get_credential()
            return Response(response)
        except Exception as e:
            print(e)

class CredentialView(APIView):
    def get(self,request,*args,**kwargs):
        from sts.sts import Sts
        from django.conf import settings
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            'domain': 'sts.tencentcloudapi.com',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 1800,
            'secret_id': settings.TENCENT_SECRET_ID,
            # 固定密钥
            'secret_key': settings.TENCENT_SECRET_KEY,
            # 设置网络代理
            # 'proxy': {
            #     'http': 'xx',
            #     'https': 'xx'
            # },
            # 换成你的 bucket
            'bucket': 'mini-1304610462',
            # 换成 bucket 所在地区
            'region': 'ap-beijing',
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': '*',
            # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
            'allow_actions': [
                # 简单上传
                'name/cos:PostObject',
                'name/cos:DeleteObject',
            ],
        }

        try:
            sts = Sts(config)
            response = sts.get_credential()
            return Response(response)
        except Exception as e:
            print(e)

class AuctionView(ListAPIView,CreateAPIView):
    queryset = models.ProductInfoRecord.objects.all().order_by('-id')

    def perform_create(self, serializer):
        token = self.request.META.get('HTTP_AUTHORIZATION',None)
        user_object = models.UserInfo.objects.filter(token=token).first()
        auction_object = serializer.save(pro_user=user_object)
        return auction_object

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializer.AuctionCreateModelSerializer
        if self.request.method == 'GET':
            return serializer.AuctionListModelSerializer

class NewsView(ListAPIView,CreateAPIView):
    # queryset = models.News.objects.prefetch_related('user','topic').order_by('-id')
    queryset = models.News.objects.all().order_by('-id')
    filter_backends = [MinFilterBackend,MaxFilterBackend]
    pagination_class = MiniLimitOffsetPagination

    def perform_create(self, serializer):
        token = self.request.META.get('HTTP_AUTHORIZATION',None)
        user_object = models.UserInfo.objects.filter(token=token).first()
        new_object = serializer.save(user=user_object)
        return new_object

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializer.NewsCreateModelSerializer
        if self.request.method == 'GET':
            return serializer.NewsListModelSerializer

class NewsDetailView(RetrieveAPIView):
    queryset = models.News.objects
    serializer_class = serializer.NewsDetailModelSerializer
    authentication_classes = [GeneralAuthentication,]

    def get(self,request,*args,**kwargs):
        response = super().get(request,*args,**kwargs)
        if not request.user:
            return response
        news_object = self.get_object() # models.News.objects.get(pk=pk)
        exists = models.ViewerRecord.objects.filter(user=request.user,news=news_object).exists()
        if not exists:
            models.ViewerRecord.objects.create(user=request.user,news=news_object)
            models.News.objects.filter(id=news_object.id).update(viewer_count = F('viewer_count') + 1)
        return response

class ProductDetail(RetrieveAPIView):
    queryset = models.ProductInfoRecord.objects
    serializer_class = serializer.AuctionDetailModelSerializer
    authentication_classes = [GeneralAuthentication, ]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if not request.user:
            return response
        product_object = self.get_object()  # models.News.objects.get(pk=pk)
        exists = models.ProductViewerRecord.objects.filter(user=request.user, product=product_object).exists()
        if not exists:
            models.ProductViewerRecord.objects.create(user=request.user, product=product_object)
            models.ProductInfoRecord.objects.filter(id=product_object.id).update(viewer_count=F('viewer_count') + 1)
        return response

class CommentView(APIView):
    def get_authenticators(self):
        if self.request.method == 'POST':
            return [UserAuthentication(),]
        return [GeneralAuthentication(),]

    def get(self,request,*args,**kwargs):
        root_id = request.query_params.get('root')
        node_queryset = models.CommentRecord.objects.filter(root_id=root_id).order_by('id')
        ser = serializer.CommentModelSerializer(instance=node_queryset,many=True)
        return Response(ser.data,status=status.HTTP_200_OK)

    def post(self,request,*args,**kwargs):
        ser = serializer.CreateCommentModelSerializer(data=request.data)
        if ser.is_valid():
            ser.save(user=request.user)
            news_id = ser.data.get('news')
            models.News.objects.filter(id=news_id).update(comment_count=F('comment_count') + 1)
            return Response(ser.data,status=status.HTTP_201_CREATED)
        return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)

class CommentAuctionView(APIView):
    def get_authenticators(self):
        if self.request.method == 'POST':
            return [UserAuthentication(),]
        return [GeneralAuthentication(),]

    def get(self,request,*args,**kwargs):
        root_id = request.query_params.get('root')
        node_queryset = models.ProductCommentRecord.objects.filter(root_id=root_id).order_by('id')
        ser = serializer.CommentAuctionModelSerializer(instance=node_queryset,many=True)
        return Response(ser.data,status=status.HTTP_200_OK)

    def post(self,request,*args,**kwargs):
        ser = serializer.CreateCommentAuctionModelSerializer(data=request.data)
        if ser.is_valid():
            ser.save(user=request.user)
            product_id = ser.data.get('product')
            models.ProductInfoRecord.objects.filter(id=product_id).update(comment_count=F('comment_count') + 1)
            return Response(ser.data,status=status.HTTP_201_CREATED)
        return Response(ser.errors,status=status.HTTP_400_BAD_REQUEST)

class CategoryView(ListAPIView):
    serializer_class = serializer.CategoryModelSerializer
    queryset = models.ProductCategoryRecord.objects.all()

class TopicView(ListAPIView):
    serializer_class = serializer.TopicModelSerializer
    queryset = models.Topic.objects.all().order_by('-count')

class TopicTitleView(APIView):
    def get(self,request,*args,**kwargs):
        topic_id = request.query_params.get('topic_id')
        token = request.META.get('HTTP_AUTHORIZATION',None)
        exists = models.TopicViewerRecord.objects.filter(user__token=token,topic_id=topic_id).exists()
        if not exists:
            user_object = models.UserInfo.objects.filter(token=token).first()
            models.TopicViewerRecord.objects.create(user=user_object,topic_id=topic_id)
            models.Topic.objects.filter(id=topic_id).update(count=F('count') + 1)
        queryset = models.Topic.objects.filter(id=topic_id).first()
        print(queryset)
        ser = serializer.TopicModelSerializer(instance=queryset,many=False)
        return Response(ser.data)

class TopicDetailView(APIView):
    def get(self,request,*args,**kwargs):
        pk = kwargs.get('pk')
        queryset = models.News.objects.filter(topic_id=pk).order_by('-id')
        if request.query_params.get('min_id'):
            res = MinFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        elif request.query_params.get('max_id'):
            res = MaxFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        else:
            result = MiniLimitOffsetPagination().paginate_queryset(queryset,request,self)
        ser = serializer.TopicDetailModelSerializer(instance=result,many=True)
        return Response(ser.data)

class MyNewsView(APIView):
    def get(self,request,*args,**kwargs):
        token = request.query_params.get('token')
        user_object = models.UserInfo.objects.filter(token=token).first()
        queryset = models.News.objects.filter(user=user_object).order_by('-id')
        if request.query_params.get('min_id'):
            res = MinFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        elif request.query_params.get('max_id'):
            res = MaxFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        else:
            result = MiniLimitOffsetPagination().paginate_queryset(queryset,request,self)
        ser = serializer.MyNewsModelSerializer(instance=result,many=True)
        return Response(ser.data)

class MyProductView(APIView):
    def get(self,request,*args,**kwargs):
        token = request.query_params.get('token')
        user_object = models.UserInfo.objects.filter(token=token).first()
        queryset = models.ProductInfoRecord.objects.filter(pro_user=user_object,bool_deal=0).order_by('-id')

        ser = serializer.MyProductModelSerializer(instance=queryset,many=True)
        return Response(ser.data)

class CollectNewsView(APIView):
    def get(self,request,*args,**kwargs):
        token = request.query_params.get('token')
        user_object = models.UserInfo.objects.filter(token=token).first()
        news_object = models.NewsCollectRecord.objects.filter(user=user_object).values('news_id')
        a = []
        for i in news_object:
            a.append(i['news_id'])
        queryset = models.News.objects.filter(id__in=a).order_by('-id')
        if request.query_params.get('min_id'):
            res = CollectMinFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        elif request.query_params.get('max_id'):
            res = CollectMaxFilterBackend().filter_queryset(request,queryset,self)
            result = MiniLimitOffsetPagination().paginate_queryset(res,request,self)
        else:
            result = MiniLimitOffsetPagination().paginate_queryset(queryset,request,self)
        ser = serializer.MyNewsModelSerializer(instance=result,many=True)
        return Response(ser.data)

class NewsAPIView(APIView):
    def get(self,request,*args,**kwargs):
        news_types = request.query_params.get('news_types')
        queryset = []
        if news_types == '1':
            queryset = models.News.objects.all().order_by('-viewer_count')[:50]
        elif news_types == '0':
            queryset = models.News.objects.all().order_by('-favor_count')[:50]
        ser = serializer.MyNewsModelSerializer(instance=queryset,many=True)
        return Response(ser.data)

class NewsFavorView(APIView):
    authentication_classes = [UserAuthentication,]

    def post(self,request,*args,**kwargs):
        ser = serializer.NewsFavorModelSerializer(data=request.data)
        if not ser.is_valid():
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        news_object = ser.validated_data.get('news')
        queryset = models.NewsFavorRecord.objects.filter(user=request.user,news=news_object)
        exists = queryset.exists()
        if exists:
            queryset.delete()
            models.News.objects.filter(id=news_object.id).update(favor_count=F('favor_count') - 1)
            count = models.News.objects.filter(id=news_object.id).first()
            return Response({'favor_count':count.favor_count},status=status.HTTP_200_OK)
        models.NewsFavorRecord.objects.create(user=request.user,news=news_object)
        models.News.objects.filter(id=news_object.id).update(favor_count=F('favor_count') + 1)
        count = models.News.objects.filter(id=news_object.id).first()
        return Response({'favor_count':count.favor_count},status=status.HTTP_201_CREATED)

class NewsCollectView(APIView):
    authentication_classes = [UserAuthentication,]

    def post(self,request,*args,**kwargs):
        ser = serializer.NewsCollectModelSerializer(data=request.data)
        if not ser.is_valid():
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        news_object = ser.validated_data.get('news')
        queryset = models.NewsCollectRecord.objects.filter(user=request.user,news=news_object)
        exists = queryset.exists()
        if exists:
            queryset.delete()
            models.News.objects.filter(id=news_object.id).update(collect_count=F('collect_count') - 1)
            count = models.News.objects.filter(id=news_object.id).first()
            return Response({'collect_count':count.collect_count},status=status.HTTP_200_OK)
        models.NewsCollectRecord.objects.create(user=request.user,news=news_object)
        models.News.objects.filter(id=news_object.id).update(collect_count=F('collect_count') + 1)
        count = models.News.objects.filter(id=news_object.id).first()
        return Response({'collect_count':count.collect_count},status=status.HTTP_201_CREATED)

class AuctionCollectView(APIView):
    authentication_classes = [UserAuthentication, ]

    def post(self, request, *args, **kwargs):
        ser = serializer.AuctionCollectModelSerializer(data=request.data)
        if not ser.is_valid():
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        product_object = ser.validated_data.get('product')
        queryset = models.ProductCollectRecord.objects.filter(user=request.user, product=product_object)
        exists = queryset.exists()
        if exists:
            queryset.delete()
            models.ProductInfoRecord.objects.filter(id=product_object.id).update(collect_count=F('collect_count') - 1)
            count = models.ProductInfoRecord.objects.filter(id=product_object.id).first()
            return Response({'collect_count': count.collect_count}, status=status.HTTP_200_OK)
        models.ProductCollectRecord.objects.create(user=request.user, product=product_object)
        models.ProductInfoRecord.objects.filter(id=product_object.id).update(collect_count=F('collect_count') + 1)
        count = models.ProductInfoRecord.objects.filter(id=product_object.id).first()
        return Response({'collect_count': count.collect_count}, status=status.HTTP_201_CREATED)

class CommentFavorView(APIView):
    authentication_classes = [UserAuthentication,]
    def post(self,request,*args,**kwargs):
        ser = serializer.CommentFavorModelSerializer(data=request.data)
        if not ser.is_valid():
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        comment_object = ser.validated_data.get('comment')
        queryset = models.CommentFavorRecord.objects.filter(user=request.user,comment=comment_object)
        exists = queryset.exists()
        if exists:
            queryset.delete()
            models.CommentRecord.objects.filter(id=comment_object.id).update(favor_count=F('favor_count') - 1)
            count = models.CommentRecord.objects.filter(id=comment_object.id).first()
            return Response({'favor_count':count.favor_count},status=status.HTTP_200_OK)
        models.CommentFavorRecord.objects.create(user=request.user,comment=comment_object)
        models.CommentRecord.objects.filter(id=comment_object.id).update(favor_count=F('favor_count') + 1)
        count = models.CommentRecord.objects.filter(id=comment_object.id).first()
        return Response({'favor_count':count.favor_count},status=status.HTTP_201_CREATED)

class FollowView(APIView):
    authentication_classes = [UserAuthentication,]

    def post(self,request,*args,**kwargs):
        ser = serializer.FollowModelSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        target_user_id = ser.validated_data.get('user')
        current_user_object = request.user
        target_user_objects = models.UserInfo.objects.filter(id=target_user_id).first()
        if target_user_objects == current_user_object:
            return Response({},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        exists = current_user_object.follow.filter(id=target_user_id).exists()
        if exists:
            current_user_object.follow.remove(target_user_id)
            models.UserInfo.objects.filter(id=target_user_id).update(fans_count=F('fans_count') - 1)
            return Response({},status=status.HTTP_200_OK)
        current_user_object.follow.add(target_user_id)
        models.UserInfo.objects.filter(id=target_user_id).update(fans_count=F('fans_count') + 1)
        return Response({},status=status.HTTP_201_CREATED)

class DealView(APIView):
    def post(self,request,*args,**kwargs):
        productList = request.data.get('productIdList')
        from_product = request.data.get('from_product')
        for i in productList:
            exists = models.DealInfoRecord.objects.filter(from_product=from_product,to_product_id=i).exists()
            if not exists:
                ser = serializer.DealCreateModelSerializer(data=request.data)
                if ser.is_valid():
                    models.DealInfoRecord.objects.create(**ser.validated_data,to_product_id=i)
                    models.ProductInfoRecord.objects.filter(id=i).update(bool_deal=1)
                    return Response({},status=status.HTTP_201_CREATED)
                return Response({},status=status.HTTP_400_BAD_REQUEST)
            return Response({},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class MyMessageView(APIView):

    def get(self,request,*args,**kwargs):
        pass

class WaitProcessView(APIView):
    authentication_classes = [UserAuthentication,]

    def get(self,request,*args,**kwargs):
        deal_product = models.DealInfoRecord.objects.all()
        context = []
        for objects in deal_product:
            if objects.to_product.pro_user == request.user:
                context.append(objects)
        ser = serializer.WaitProcessModelSerializer(instance=context,many=True)
        return Response(ser.data)









