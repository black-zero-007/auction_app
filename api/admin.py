from django.contrib import admin
from api import models
# Register your models here.
admin.site.register(models.UserInfo)

admin.site.register(models.News)
admin.site.register(models.NewsCollectRecord)
admin.site.register(models.NewsFavorRecord)
admin.site.register(models.CommentRecord)
admin.site.register(models.ViewerRecord)
admin.site.register(models.Topic)

admin.site.register(models.ProductInfoRecord)
admin.site.register(models.ProductCommentRecord)
admin.site.register(models.ProductCategoryRecord)
admin.site.register(models.ProductCollectRecord)
admin.site.register(models.ProductViewerRecord)
admin.site.register(models.DealInfoRecord)





