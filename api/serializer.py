# Author:JZW
import re
from django_redis import get_redis_connection

from api import models
from django.forms import model_to_dict
from rest_framework import serializers
from rest_framework import exceptions
from rest_framework.exceptions import ValidationError

def phone_validator(value):
    if not re.match(r"^1[3|4|5|6|7|8]\d{9}$",value):
        raise ValidationError('手机格式错误')

class MessageSerializer(serializers.Serializer):
    phone = serializers.CharField(label='手机号',validators=[phone_validator,])

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(label='手机号',validators=[phone_validator,])
    code = serializers.CharField(label='短信验证码')
    wx_code = serializers.CharField(label='微信临时登录凭证')
    nickname = serializers.CharField(label='微信昵称')
    avatar = serializers.CharField(label='微信头像')

    #定义钩子函数
    def validate_code(self,value):
        if len(value) != 6:
            raise ValidationError('短信格式错误')
        if not value.isdecimal():
            raise ValidationError('短信格式错误')

        phone = self.initial_data.get('phone')
        conn = get_redis_connection()
        code = conn.get(phone)
        print(code)
        if not code:
            raise ValidationError('验证码已过期')
        if value != code.decode('utf-8'):
            raise ValidationError('验证码错误')

        return value

class NewsDetailCreateModelSerializer(serializers.Serializer):
    cos_path = serializers.CharField()
    key = serializers.CharField()

class NewsCreateModelSerializer(serializers.ModelSerializer):
    imageList = NewsDetailCreateModelSerializer(many=True)

    class Meta:
        model = models.News
        exclude = ['viewer_count','comment_count','favor_count','user']

    def create(self, validated_data):
        image_List = validated_data.pop('imageList')
        new_object = models.News.objects.create(**validated_data)
        data_list = models.NewsDetail.objects.bulk_create(
            [models.NewsDetail(**info,news=new_object) for info in image_List]
        )
        new_object.imageList = data_list

        if new_object.topic:
            new_object.topic.count += 1
            new_object.save()
        return new_object

class NewsListModelSerializer(serializers.ModelSerializer):
    topic = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = models.News
        fields = ['id','cover','content','topic',"user",'favor_count','viewer_count']

    def get_topic(self,obj):
        if not obj.topic:
            return
        return model_to_dict(obj.topic,['id','title'])

    def get_user(self,obj):
        return model_to_dict(obj.user,['id','nickname','avatar'])

    def get_content(self,obj):
        news_content = obj.content[0:10]
        return news_content

class NewsDetailModelSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    images = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()

    viewer = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

    is_favor = serializers.SerializerMethodField()
    is_collect = serializers.SerializerMethodField()

    class Meta:
        model = models.News
        exclude = ['cover',]
        # fields   = '__all__'

    def get_images(self,obj):
        detail_queryset = models.NewsDetail.objects.filter(news=obj)
        return [model_to_dict(row,['id','cos_path'])for row in detail_queryset]
    def get_user(self,obj):
        context =  model_to_dict(obj.user,fields=['id','nickname','avatar','token'])
        user_object = self.context['request'].user
        if not user_object:
            return context
        follow = user_object.follow.filter(id=obj.user_id).exists()
        context['follow'] = follow
        return context
    def get_topic(self,obj):
        if not obj.topic:
            return
        return model_to_dict(obj.topic,fields=['id','title'])
    def get_viewer(self,obj):
        queryset = models.ViewerRecord.objects.filter(news_id=obj.id)
        viewer_queryset_list = queryset.order_by('-id')[0:10]
        context = {
            'count':queryset.count(),
            'result':[model_to_dict(row.user,fields=['nickname','avatar']) for row in viewer_queryset_list]
        }
        return context
    def get_comment(self,obj):
        user_object = self.context['request'].user
        first_queryset = models.CommentRecord.objects.filter(news=obj,depth=1).order_by('id').values(
            'id',
            'comment',
            'depth',
            'user__nickname',
            'user__avatar',
            'create_date',
            'favor_count'
        )
        first_id_list = [item['id'] for item in first_queryset]
        from django.db.models import Max
        result = models.CommentRecord.objects.filter(news=obj,depth=2,reply_id__in=first_id_list).values('reply_id').annotate(max_id=Max('id'))
        second_id_list = [item['max_id'] for item in result]
        second_queryset = models.CommentRecord.objects.filter(id__in=second_id_list).values(
            'id',
            'comment',
            'depth',
            'user__nickname',
            'user__avatar',
            'create_date',
            'reply_id',
            'reply__user__nickname',
            'favor_count'
        )
        import collections
        first_dict = collections.OrderedDict()
        for item in first_queryset:
            item['create_date'] = item['create_date'].strftime('%Y-%m-%d')
            first_dict[item['id']] = item
            exists = models.CommentFavorRecord.objects.filter(comment=item['id'],user=user_object).exists()
            count = models.CommentRecord.objects.filter(root_id=item['id']).count()
            item['is_comment'] = exists
            if count < 2:
               item['getmore'] = False
            else:
                item['getmore'] = True
        for node in second_queryset:
            first_dict[node['reply_id']]['child'] = [node,]
            exists = models.CommentFavorRecord.objects.filter(comment=node['id'], user=user_object).exists()
            node['is_comment'] = exists
        return first_dict.values()
    def get_is_favor(self,obj):
        user_object = self.context['request'].user #上下文
        # 用户未登录
        if not user_object:
            return False
        #用户登录
        exists = models.NewsFavorRecord.objects.filter(user=user_object,news=obj).exists()
        context = exists
        return context
    def get_is_collect(self,obj):
        user_object = self.context['request'].user
        if not user_object:
            return False
        exists = models.NewsCollectRecord.objects.filter(user=user_object,news=obj).exists()
        context = exists
        return context

class AuctionListModelSerializer(serializers.ModelSerializer):
    datatime = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    images = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductInfoRecord
        exclude = ['wx_phone',]

    def get_images(self,obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj)
        return [model_to_dict(row, ['id','cos_path']) for row in detail_queryset]

    def get_user(self,obj):
        return model_to_dict(obj.pro_user,['id','nickname','avatar'])

    def get_category(self,obj):
        return model_to_dict(obj.category,['id','category'])

class AuctionCreateModelSerializer(serializers.ModelSerializer):
    imageList = NewsDetailCreateModelSerializer(many=True)

    class Meta:
        model = models.ProductInfoRecord
        exclude = ['viewer_count', 'collect_count', 'pro_user']

    def create(self, validated_data):
        image_List = validated_data.pop('imageList')
        pro_object = models.ProductInfoRecord.objects.create(**validated_data)
        data_list = models.ProductDetail.objects.bulk_create(
            [models.ProductDetail(**info, auction=pro_object) for info in image_List]
        )
        pro_object.imageList = data_list

        return pro_object

class AuctionDetailModelSerializer(serializers.ModelSerializer):

    images = serializers.SerializerMethodField()
    pro_user = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    viewer = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

    is_collect = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductInfoRecord
        exclude = ['address','price','datatime']
        # fields   = '__all__'

    def get_images(self, obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj)
        return [model_to_dict(row, ['id', 'cos_path']) for row in detail_queryset]

    def get_pro_user(self, obj):
        context = model_to_dict(obj.pro_user, fields=['id', 'nickname', 'avatar','token'])
        user_object = self.context['request'].user
        if not user_object:
            return context
        follow = user_object.follow.filter(id=obj.pro_user_id).exists()
        context['follow'] = follow
        return context

    def get_category(self, obj):
        return model_to_dict(obj.category, fields=['id', 'category'])

    def get_viewer(self, obj):
        queryset = models.ProductViewerRecord.objects.filter(product_id=obj.id)
        viewer_queryset_list = queryset.order_by('-id')[0:10]
        context = {
            'count': queryset.count(),
            'result': [model_to_dict(row.user, fields=['nickname', 'avatar']) for row in viewer_queryset_list]
        }
        return context

    def get_comment(self, obj):
        user_object = self.context['request'].user
        first_queryset = models.ProductCommentRecord.objects.filter(product=obj, depth=1).order_by('id').values(
            'id',
            'comment',
            'depth',
            'user__nickname',
            'user__avatar',
            'create_date',
        )
        first_id_list = [item['id'] for item in first_queryset]
        from django.db.models import Max
        result = models.ProductCommentRecord.objects.filter(product=obj, depth=2, reply_id__in=first_id_list).values(
            'reply_id').annotate(max_id=Max('id'))
        second_id_list = [item['max_id'] for item in result]
        second_queryset = models.ProductCommentRecord.objects.filter(id__in=second_id_list).values(
            'id',
            'comment',
            'depth',
            'user__nickname',
            'user__avatar',
            'create_date',
            'reply_id',
            'reply__user__nickname',
        )
        import collections
        first_dict = collections.OrderedDict()
        for item in first_queryset:
            item['create_date'] = item['create_date'].strftime('%Y-%m-%d')
            first_dict[item['id']] = item
            count = models.ProductCommentRecord.objects.filter(root_id=item['id']).count()
            if count < 2:
                item['getmore'] = False
            else:
                item['getmore'] = True
        for node in second_queryset:
            first_dict[node['reply_id']]['child'] = [node, ]
        return first_dict.values()

    def get_is_collect(self, obj):
        user_object = self.context['request'].user
        if not user_object:
            return False
        exists = models.ProductCollectRecord.objects.filter(user=user_object, product=obj).exists()
        context = exists
        return context

class HomeModelSerializer(serializers.ModelSerializer):
    follow_count = serializers.SerializerMethodField()
    # comment_favor = serializers.SerializerMethodField()
    collect_count = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()
    follow_user = serializers.SerializerMethodField()
    fans_user = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = models.UserInfo
        exclude = ['balance','session_key','openid']

    def get_follow_count(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        count = user_object.follow.all().count()
        return count
    def get_collect_count(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        news_count = models.NewsCollectRecord.objects.filter(user=user_object).count()
        product_count = models.ProductCollectRecord.objects.filter(user=user_object,product__bool_deal=0).count()
        context = [
            {'news_count':news_count},
            {'product_count':product_count}
        ]
        return context
    def get_article_count(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        count = models.News.objects.filter(user=user_object).count()
        return count
    def get_follow_user(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        exists = user_object.follow.all().exists()
        if exists:
            user = user_object.follow.all().values('nickname','avatar','fans_count','id')
            context = {
                'user': user,
                'exists': exists
            }
            return context

        context = {
            'exists':exists
        }
        return context
    def get_fans_user(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        exists = user_object.userinfo_set.all().exists()
        if not exists:
            context = {
                'exists':exists
            }
            return context
        user = user_object.userinfo_set.all().values('nickname','avatar','fans_count','id')
        context = {
            'exists':exists,
            'user':user
        }
        return context
    def get_product_count(self,obj):
        user_object = models.UserInfo.objects.filter(token=obj.token).first()
        count = models.ProductInfoRecord.objects.filter(pro_user=user_object,bool_deal=0).count()
        return count

class ChangeInfoSchoolModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserInfo
        fields = ['school']

class ChangeInfoColleageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = ['colleage']

class CommentModelSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    user__nickname = serializers.CharField(source='user.nickname',read_only=True)
    user__avatar = serializers.CharField(source='user.avatar',read_only=True)
    reply_id = serializers.CharField(source='reply.id',read_only=True)
    reply__user__nickname = serializers.CharField(source='reply.user.nickname',read_only=True)
    is_comment = serializers.SerializerMethodField()

    class Meta:
        model = models.CommentRecord
        exclude = ['user',]
    def get_is_comment(self,obj):
        exists = models.CommentFavorRecord.objects.filter(comment=obj.id).exists()
        return exists

class CommentAuctionModelSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    user__nickname = serializers.CharField(source='user.nickname', read_only=True)
    user__avatar = serializers.CharField(source='user.avatar', read_only=True)
    reply_id = serializers.CharField(source='reply.id', read_only=True)
    reply__user__nickname = serializers.CharField(source='reply.user.nickname', read_only=True)

    class Meta:
        model = models.ProductCommentRecord
        exclude = ['user', ]

class CreateCommentModelSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    user__nickname = serializers.CharField(source='user.nickname', read_only=True)
    user__avatar = serializers.CharField(source='user.avatar', read_only=True)
    reply_id = serializers.CharField(source='reply.id', read_only=True)
    reply__user__nickname = serializers.CharField(source='reply.user.nickname', read_only=True)

    class Meta:
        model = models.CommentRecord
        # fields = "__all__"
        exclude = ['user',]

class CreateCommentAuctionModelSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    user__nickname = serializers.CharField(source='user.nickname', read_only=True)
    user__avatar = serializers.CharField(source='user.avatar', read_only=True)
    reply_id = serializers.CharField(source='reply.id', read_only=True)
    reply__user__nickname = serializers.CharField(source='reply.user.nickname', read_only=True)

    class Meta:
        model = models.ProductCommentRecord
        # fields = "__all__"
        exclude = ['user', ]

class TopicDetailModelSerializer(serializers.ModelSerializer):
    topic = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = models.News
        fields = ['id','cover','content','topic',"user",'favor_count','viewer_count','topic_count']

    def get_topic(self,obj):
        return model_to_dict(obj.topic, ['id', 'title','count'])

    def get_user(self,obj):
        return model_to_dict(obj.user,['id','nickname','avatar'])

    def get_content(self,obj):
        news_content = obj.content[0:10]
        return news_content

    def get_topic_count(self,obj):
        queryset = models.News.objects.filter(topic_id=obj.topic.id)
        context = queryset.count()
        return context

class NewsFavorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NewsFavorRecord
        fields = ['news']

class NewsCollectModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NewsCollectRecord
        fields = ['news']

class AuctionCollectModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCollectRecord
        fields = ['product']

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategoryRecord
        fields = '__all__'

class TopicModelSerializer(serializers.ModelSerializer):
    topic = serializers.SerializerMethodField()
    class Meta:
        model = models.Topic
        fields = '__all__'

    def get_topic(self,obj):
        queryset = models.News.objects.filter(topic_id=obj.id)
        context = {
            'count':queryset.count()
        }
        return context

class CommentFavorModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CommentFavorRecord
        fields = ['comment']

class FollowModelSerializer(serializers.Serializer):
    user = serializers.IntegerField(label='要关注用户ID')

    def validate_user(self,value):
        exists = models.UserInfo.objects.filter(id=value).exists()
        if not exists:
            raise exceptions.ValidationError('用户不存在')
        return value

class MyNewsModelSerializer(serializers.ModelSerializer):
    topic = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = models.News
        fields = ['id', 'cover', 'content', 'topic', 'user',  'viewer_count']

    def get_topic(self, obj):
        if not obj.topic:
            return
        return model_to_dict(obj.topic, ['id', 'title'])

    def get_user(self, obj):
        return model_to_dict(obj.user, ['id', 'nickname', 'avatar'])

    def get_content(self, obj):
        news_content = obj.content[0:10]
        return news_content

class MyProductModelSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductInfoRecord
        fields = ['id', 'product_name', 'category', 'pro_user','cover','viewer_count','user']

    def get_cover(self,obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj).first()
        return [model_to_dict(detail_queryset, ['id', 'cos_path'])]

    def get_category(self,obj):
        return model_to_dict(obj.category,['id','category'])

    def get_user(self, obj):
        return model_to_dict(obj.pro_user, ['id', 'nickname', 'avatar'])

class DealListModelSerializer(serializers.Serializer):
    from_product_id = serializers.IntegerField(label='交易物品Id')
    agree = serializers.IntegerField()

class DealCreateModelSerializer(serializers.ModelSerializer):
    productIdList = serializers.SerializerMethodField()

    class Meta:
        model = models.DealInfoRecord
        exclude = ['datatime','finish_time','to_product']

class WaitProcessModelSerializer(serializers.ModelSerializer):
    datatime = serializers.DateTimeField(format="%Y-%m-%d")
    finish_time = serializers.DateTimeField(format="%Y-%m-%d")
    from_product_avatar = serializers.SerializerMethodField()
    from_product_category = serializers.SerializerMethodField()
    from_productinfo = serializers.SerializerMethodField()

    class Meta:
        model = models.DealInfoRecord
        fields = '__all__'

    def get_from_productinfo(self,obj):
        from_product = models.ProductInfoRecord.objects.filter(id=obj.from_product.id)
        return [model_to_dict(row, ['id', 'product_name','pro_user','price','address']) for row in from_product]

    def get_from_product_avatar(self,obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj.from_product)
        return [model_to_dict(row, ['id', 'cos_path']) for row in detail_queryset]

    def get_from_product_category(self,obj):
        product_object = models.ProductInfoRecord.objects.filter(id=obj.from_product.id).first()
        category = models.ProductCategoryRecord.objects.filter(id=product_object.category.id).first()
        return model_to_dict(category,['category'])

class WaitAuctionModelSerializer(serializers.ModelSerializer):
    datatime = serializers.DateTimeField(format="%Y-%m-%d")
    from_product_avatar = serializers.SerializerMethodField()
    from_product_category = serializers.SerializerMethodField()
    from_productinfo = serializers.SerializerMethodField()

    class Meta:
        model = models.DealInfoRecord
        exclude = ['finish_time']

    def get_from_productinfo(self,obj):
        from_product = models.ProductInfoRecord.objects.filter(id=obj.from_product.id)
        return [model_to_dict(row, ['id', 'product_name','pro_user','price','address']) for row in from_product]

    def get_from_product_avatar(self,obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj.from_product)
        return [model_to_dict(row, ['id', 'cos_path']) for row in detail_queryset]

    def get_from_product_category(self,obj):
        product_object = models.ProductInfoRecord.objects.filter(id=obj.from_product.id).first()
        category = models.ProductCategoryRecord.objects.filter(id=product_object.category.id).first()
        return model_to_dict(category,['category'])

class HaveAuctionModelSerializer(serializers.ModelSerializer):
    datatime = serializers.DateTimeField(format="%Y-%m-%d")
    from_product_avatar = serializers.SerializerMethodField()
    from_product_category = serializers.SerializerMethodField()
    from_productinfo = serializers.SerializerMethodField()

    class Meta:
        model = models.DealInfoRecord
        exclude = ['finish_time']

    def get_from_productinfo(self,obj):
        from_product = models.ProductInfoRecord.objects.filter(id=obj.from_product.id)
        return [model_to_dict(row, ['id', 'product_name','pro_user','price','address']) for row in from_product]

    def get_from_product_avatar(self,obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj.from_product)
        return [model_to_dict(row, ['id', 'cos_path']) for row in detail_queryset]

    def get_from_product_category(self,obj):
        product_object = models.ProductInfoRecord.objects.filter(id=obj.from_product.id).first()
        category = models.ProductCategoryRecord.objects.filter(id=product_object.category.id).first()
        return model_to_dict(category,['category'])

class DealAuctionModelSerializer(serializers.ModelSerializer):
    datatime = serializers.DateTimeField(format="%Y-%m-%d")
    from_product_avatar = serializers.SerializerMethodField()
    from_product_category = serializers.SerializerMethodField()
    from_productinfo = serializers.SerializerMethodField()
    to_productinfo = serializers.SerializerMethodField()

    class Meta:
        model = models.DealInfoRecord
        exclude = ['finish_time']

    def get_from_productinfo(self, obj):
        from_product = models.ProductInfoRecord.objects.filter(id=obj.from_product.id)
        return [model_to_dict(row, ['id', 'product_name', 'pro_user', 'price', 'address']) for row in from_product]

    def get_from_product_avatar(self, obj):
        detail_queryset = models.ProductDetail.objects.filter(auction=obj.from_product)
        return [model_to_dict(row, ['id', 'cos_path']) for row in detail_queryset]

    def get_from_product_category(self, obj):
        product_object = models.ProductInfoRecord.objects.filter(id=obj.from_product.id).first()
        category = models.ProductCategoryRecord.objects.filter(id=product_object.category.id).first()
        return model_to_dict(category, ['category'])

    def get_to_productinfo(self, obj):
        to_product = models.ProductInfoRecord.objects.filter(id=obj.to_product.id).first()
        category = models.ProductCategoryRecord.objects.filter(id=to_product.category.id).first()
        detail_queryset = models.ProductDetail.objects.filter(auction=obj.to_product).first()
        context = []
        context.append(model_to_dict(to_product, ['id', 'product_name', 'pro_user', 'price', 'address']))
        context.append(model_to_dict(category, ['category']))
        context.append(model_to_dict(detail_queryset, ['id', 'cos_path']))
        return context

class CategoryProductModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ProductInfoRecord
        fields = '__all__'

class ProductDelModelView(serializers.ModelSerializer):

    class Meta:
        model = models.ProductInfoRecord
        fields = ['product_name']

class NewsDelModelView(serializers.ModelSerializer):

    class Meta:
        model = models.News
        fields = ['content']






