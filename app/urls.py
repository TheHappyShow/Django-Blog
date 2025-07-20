from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', ArticleListView.as_view(), name='feed'),
    path('create/', ArticleCreateView.as_view(), name='article_create'),
    path('search/', ArticleSearchView.as_view(), name='article_search'),
    path('update/<slug:slug>/', ArticleUpdateView.as_view(), name='article_update'),
    path('delete/<int:pk>/', ArticleDeleteView.as_view(), name='article_delete'),
    path("blog/<slug:slug>/", ArticleDetailView.as_view(), name='post-detail'),
    path("category/<slug:slug>/", ArticleCatListView.as_view(), name='category_article_list'),
    path('login', CustomLoginView.as_view(), name='login'),
    path('registration', CustomRegistrationView.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('create_comment/<slug:slug>/', CommentCreateView.as_view(), name='comment_create'),
    path('otp/', OTPVerifyView.as_view(), name='otp')
]