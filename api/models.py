from django.db import models

# Create your models here.
class UserInfo(models.Model):
    phone = models.CharField(verbose_name='手机号',max_length=11,unique=True)
    nickname = models.CharField(verbose_name='昵称',max_length=64)
    avatar = models.CharField(verbose_name='头像',max_length=256,null=True)
    token = models.CharField(verbose_name='用户Token',max_length=64,blank=True)
    city = models.CharField(verbose_name='城市',max_length=16,default='大连')
    gender = models.PositiveIntegerField(verbose_name='性别',default=1)
    school = models.CharField(verbose_name='学校名称',max_length=32,blank=True,null=True)
    colleage = models.CharField(verbose_name='学院名称',max_length=16,blank=True,null=True)

    fans_count = models.PositiveIntegerField(verbose_name='粉丝数',default=0)
    follow = models.ManyToManyField(verbose_name='关注',to='self',blank=True,symmetrical=False)

    balance = models.PositiveIntegerField(verbose_name='账户余额',default=0)
    session_key = models.CharField(verbose_name='微信会话密钥',max_length=32)
    openid = models.CharField(verbose_name='微信用户唯一标识',max_length=32)

    def __str__(self):
        return self.nickname

    class Meta:
        verbose_name = '小程序用户信息'
        verbose_name_plural = verbose_name

class Topic(models.Model):
    """
    话题
    """
    title = models.CharField(verbose_name='话题',max_length=64)
    count = models.PositiveIntegerField(verbose_name='关注度',default=0)


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '话题管理'
        verbose_name_plural = verbose_name

class News(models.Model):
    """
    动态
    """
    cover = models.CharField(verbose_name='封面',max_length=128)
    content = models.CharField(verbose_name='内容',max_length=255)
    topic = models.ForeignKey(verbose_name='话题',to='Topic',null=True,blank=True,on_delete=models.CASCADE)
    address = models.CharField(verbose_name='位置',max_length=128,null=True,blank=True)

    user = models.ForeignKey(verbose_name='发布者',to='UserInfo',related_name='news',on_delete=models.CASCADE)

    favor_count = models.PositiveIntegerField(verbose_name='点赞数',default=0)
    viewer_count = models.PositiveIntegerField(verbose_name='浏览数',default=0)
    comment_count = models.PositiveIntegerField(verbose_name='评论数',default=0)
    collect_count = models.PositiveIntegerField(verbose_name='收藏数',default=0)
    create_time = models.DateTimeField(verbose_name='发布时间',auto_now_add=True)

    def __str__(self):
        return self.content[0:10]

    class Meta:
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name

class NewsDetail(models.Model):
    key = models.CharField(verbose_name='腾讯对象存储中文件名',max_length=128,help_text='用于以后在腾讯对象存储中删除')
    cos_path = models.CharField(verbose_name='腾讯对象存储中图片路径',max_length=128)
    news = models.ForeignKey(verbose_name='动态',to='News',on_delete=models.CASCADE)

    def __str__(self):
        return self.news.content[0:10]

    class Meta:
        verbose_name = '文章图片管理'
        verbose_name_plural = verbose_name

class ViewerRecord(models.Model):
    """
    浏览记录
    """
    user = models.ForeignKey(verbose_name='用户',to='UserInfo',on_delete=models.CASCADE)
    news = models.ForeignKey(verbose_name='动态',to='News',on_delete=models.CASCADE)

    def __str__(self):
        return self.news.content[0:10]

    class Meta:
        verbose_name = '文章浏览记录'
        verbose_name_plural = verbose_name

class TopicViewerRecord(models.Model):
    user = models.ForeignKey(verbose_name='用户',to=UserInfo,on_delete=models.CASCADE)
    topic = models.ForeignKey(verbose_name='话题',to=Topic,on_delete=models.CASCADE)

    def __str__(self):
        return self.topic.title

    class Meta:
        verbose_name = '话题浏览管理'
        verbose_name_plural = verbose_name

class NewsFavorRecord(models.Model):
    """
    动态点赞记录表
    """
    user = models.ForeignKey(verbose_name='点赞用户', to='UserInfo', on_delete=models.CASCADE)
    news = models.ForeignKey(verbose_name='动态', to='News', on_delete=models.CASCADE)

    def __str__(self):
        return self.news.content[0:10]

    class Meta:
        verbose_name = '文章点赞管理'
        verbose_name_plural = verbose_name

class CommentRecord(models.Model):
    """
    评论表
    """
    comment = models.CharField(verbose_name='评论内容',max_length=255)
    user = models.ForeignKey(verbose_name='评论者',to='UserInfo',on_delete=models.CASCADE)
    news = models.ForeignKey(verbose_name='动态',to='News',on_delete=models.CASCADE)
    create_date = models.DateTimeField(verbose_name='评论时间',auto_now_add=True)

    reply = models.ForeignKey(verbose_name='回复对象',to='self',null=True,blank=True,related_name='replys',on_delete=models.CASCADE)
    depth = models.PositiveIntegerField(verbose_name='层级数',default=1)
    root = models.ForeignKey(verbose_name='根评论',to='self',blank=True,null=True,related_name='roots',on_delete=models.CASCADE)
    favor_count = models.PositiveIntegerField(verbose_name='点赞数',default=0)

    def __str__(self):
        return self.news.content[0:10]

    class Meta:
        verbose_name = '文章评论管理'
        verbose_name_plural = verbose_name

class CommentFavorRecord(models.Model):
    """
    评论赞
    """
    comment = models.ForeignKey(verbose_name='评论',to='CommentRecord',on_delete=models.CASCADE)
    user = models.ForeignKey(verbose_name='用户',to='UserInfo',on_delete=models.CASCADE)

    def __str__(self):
        return self.comment

    class Meta:
        verbose_name = '文章评论点赞管理'
        verbose_name_plural = verbose_name

class NewsCollectRecord(models.Model):
    """
    文章收藏表
    """
    user = models.ForeignKey(verbose_name='用户',to=UserInfo,on_delete=models.CASCADE)
    news = models.ForeignKey(verbose_name='文章',to=News,on_delete=models.CASCADE)

    def __str__(self):
        return self.news.content[0:10]

    class Meta:
        verbose_name = '文章收藏管理'
        verbose_name_plural = verbose_name

class ProductInfoRecord(models.Model):
    product_name = models.CharField(verbose_name='商品名称',max_length=16)
    product_info = models.CharField(verbose_name='商品详情',max_length=255)
    wx_phone = models.CharField(verbose_name='联系方式',max_length=16)
    address = models.CharField(verbose_name='位置', max_length=128)

    category = models.ForeignKey(verbose_name='分类',to='ProductCategoryRecord',on_delete=models.CASCADE)
    price = models.PositiveIntegerField(verbose_name='价格')
    collect_count = models.PositiveIntegerField(verbose_name='收藏数',default=0)
    viewer_count = models.PositiveIntegerField(verbose_name='浏览数',default=0)
    comment_count = models.PositiveIntegerField(verbose_name='评论数',default=0)

    datatime = models.DateTimeField(verbose_name='发布时间',auto_now_add=True)

    pro_user = models.ForeignKey(verbose_name='发布者',to='UserInfo',related_name='product',on_delete=models.CASCADE)
    bool_deal = models.PositiveIntegerField(verbose_name='交易状态',default=0)

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = '商品信息管理'
        verbose_name_plural = verbose_name

class ProductDetail(models.Model):
    key = models.CharField(verbose_name='腾讯对象存储中文件名', max_length=128, help_text='用于以后在腾讯对象存储中删除')
    cos_path = models.CharField(verbose_name='腾讯对象存储中图片路径', max_length=128)
    auction = models.ForeignKey(verbose_name='商品', to='ProductInfoRecord', on_delete=models.CASCADE)

    def __str__(self):
        return self.auction.product_name

    class Meta:
        verbose_name = '商品图片管理'
        verbose_name_plural = verbose_name

class ProductCategoryRecord(models.Model):
    category = models.CharField(verbose_name='分类',max_length=16)
    key = models.CharField(verbose_name='腾讯对象存储中文件名', max_length=128, help_text='用于以后在腾讯对象存储中删除',default=0)
    cos_path = models.CharField(verbose_name='腾讯对象存储中图片路径', max_length=128,default=0)


    def __str__(self):
        return self.category

    class Meta:
        verbose_name = '分类管理'
        verbose_name_plural = verbose_name

class ProductCollectRecord(models.Model):
    """
        商品收藏表
        """
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', on_delete=models.CASCADE)
    product = models.ForeignKey(verbose_name='商品', to='ProductInfoRecord', on_delete=models.CASCADE)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = '商品收藏管理'
        verbose_name_plural = verbose_name

class ProductViewerRecord(models.Model):
    product = models.ForeignKey(verbose_name='商品',to='ProductInfoRecord',on_delete=models.CASCADE)
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', on_delete=models.CASCADE)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = '商品浏览管理'
        verbose_name_plural = verbose_name

class ProductCommentRecord(models.Model):
    comment = models.CharField(verbose_name='评论内容', max_length=255)
    user = models.ForeignKey(verbose_name='评论者', to='UserInfo', on_delete=models.CASCADE)
    product = models.ForeignKey(verbose_name='商品', to='ProductInfoRecord', on_delete=models.CASCADE)
    create_date = models.DateTimeField(verbose_name='评论时间', auto_now_add=True)

    reply = models.ForeignKey(verbose_name='回复对象', to='self', null=True, blank=True, related_name='replys',
                              on_delete=models.CASCADE)
    depth = models.PositiveIntegerField(verbose_name='层级数', default=1)
    root = models.ForeignKey(verbose_name='根评论', to='self', blank=True, null=True, related_name='roots',
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = '商品评论管理'
        verbose_name_plural = verbose_name

class DealInfoRecord(models.Model):
    from_product = models.ForeignKey(verbose_name='被交易物品',to='ProductInfoRecord',related_name='from_product',on_delete=models.CASCADE)
    to_product = models.ForeignKey(verbose_name='交易物品',to='ProductInfoRecord',related_name='to_product',on_delete=models.CASCADE)

    performance = models.PositiveIntegerField(verbose_name='完成情况',default=0)
    agreement = models.PositiveIntegerField(verbose_name='是否同意',default=0)

    datatime = models.DateTimeField(verbose_name='交易时间',auto_now_add=True)
    finish_time = models.DateTimeField(verbose_name='完成交易时间',auto_now=True)

    address = models.CharField(verbose_name='交易地点',max_length=32)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = '订单信息管理'
        verbose_name_plural = verbose_name






