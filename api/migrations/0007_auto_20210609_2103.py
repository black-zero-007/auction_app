# Generated by Django 3.1.4 on 2021-06-09 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20210609_1526'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commentfavorrecord',
            options={'verbose_name': '文章评论点赞管理', 'verbose_name_plural': '文章评论点赞管理'},
        ),
        migrations.AlterModelOptions(
            name='commentrecord',
            options={'verbose_name': '文章评论管理', 'verbose_name_plural': '文章评论管理'},
        ),
        migrations.AlterModelOptions(
            name='dealinforecord',
            options={'verbose_name': '订单信息管理', 'verbose_name_plural': '订单信息管理'},
        ),
        migrations.AlterModelOptions(
            name='news',
            options={'verbose_name': '文章管理', 'verbose_name_plural': '文章管理'},
        ),
        migrations.AlterModelOptions(
            name='newscollectrecord',
            options={'verbose_name': '文章收藏管理', 'verbose_name_plural': '文章收藏管理'},
        ),
        migrations.AlterModelOptions(
            name='newsdetail',
            options={'verbose_name': '文章图片管理', 'verbose_name_plural': '文章图片管理'},
        ),
        migrations.AlterModelOptions(
            name='newsfavorrecord',
            options={'verbose_name': '文章点赞管理', 'verbose_name_plural': '文章点赞管理'},
        ),
        migrations.AlterModelOptions(
            name='productcategoryrecord',
            options={'verbose_name': '分类管理', 'verbose_name_plural': '分类管理'},
        ),
        migrations.AlterModelOptions(
            name='productcollectrecord',
            options={'verbose_name': '商品收藏管理', 'verbose_name_plural': '商品收藏管理'},
        ),
        migrations.AlterModelOptions(
            name='productcommentrecord',
            options={'verbose_name': '商品评论管理', 'verbose_name_plural': '商品评论管理'},
        ),
        migrations.AlterModelOptions(
            name='productdetail',
            options={'verbose_name': '商品图片管理', 'verbose_name_plural': '商品图片管理'},
        ),
        migrations.AlterModelOptions(
            name='productinforecord',
            options={'verbose_name': '商品信息管理', 'verbose_name_plural': '商品信息管理'},
        ),
        migrations.AlterModelOptions(
            name='productviewerrecord',
            options={'verbose_name': '商品浏览管理', 'verbose_name_plural': '商品浏览管理'},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'verbose_name': '话题管理', 'verbose_name_plural': '话题管理'},
        ),
        migrations.AlterModelOptions(
            name='topicviewerrecord',
            options={'verbose_name': '话题浏览管理', 'verbose_name_plural': '话题浏览管理'},
        ),
        migrations.AlterModelOptions(
            name='userinfo',
            options={'verbose_name': '小程序用户信息', 'verbose_name_plural': '小程序用户信息'},
        ),
        migrations.AlterModelOptions(
            name='viewerrecord',
            options={'verbose_name': '文章浏览记录', 'verbose_name_plural': '文章浏览记录'},
        ),
        migrations.AddField(
            model_name='productcategoryrecord',
            name='cos_path',
            field=models.CharField(default=0, max_length=128, verbose_name='腾讯对象存储中图片路径'),
        ),
        migrations.AddField(
            model_name='productcategoryrecord',
            name='key',
            field=models.CharField(default=0, help_text='用于以后在腾讯对象存储中删除', max_length=128, verbose_name='腾讯对象存储中文件名'),
        ),
    ]