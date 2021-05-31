# Author:JZW
from django.urls import path,re_path
from api import views


urlpatterns = [
    path('login/',views.LoginView.as_view()),
    path('message/',views.MessagesView.as_view()),
    path('credential/',views.CredentialView.as_view()),
    path('credentialtwo/',views.CredentialTwoView.as_view()),
    path('auction/',views.AuctionView.as_view()),
    path('News/',views.NewsView.as_view()),
    path('comment/',views.CommentView.as_view()),
    path('commentauction/',views.CommentAuctionView.as_view()),
    path('newsfavor/',views.NewsFavorView.as_view()),
    path('newscollect/',views.NewsCollectView.as_view()),
    path('auctioncollect/',views.AuctionCollectView.as_view()),
    path('commentfavor/',views.CommentFavorView.as_view()),
    path('category/',views.CategoryView.as_view()),
    path('topic/',views.TopicView.as_view()),
    path('topicTitle/',views.TopicTitleView.as_view()),
    path('follow/',views.FollowView.as_view()),
    path('home/',views.HomeView.as_view()),
    path('myNews/',views.MyNewsView.as_view()),
    path('myProduct/',views.MyProductView.as_view()),
    path('collectNews/',views.CollectNewsView.as_view()),
    path('newsAPI/',views.NewsAPIView.as_view()),
    path('deal/',views.DealView.as_view()),
    path('mymessage/',views.MyMessageView.as_view()),
    path('waitprocess/',views.WaitProcessView.as_view()),
    re_path('topic/(?P<pk>\d+)/$',views.TopicDetailView.as_view()),
    re_path('News/(?P<pk>\d+)/$',views.NewsDetailView.as_view()),
    re_path('auction/(?P<pk>\d+)/$',views.ProductDetail.as_view()),
]