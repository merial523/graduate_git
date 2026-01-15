from django.urls import path
from . import views

app_name = "administer"
urlpatterns = [
    path('', views.administer_index, name = "administer_index"), #アドミンのトップページ
    path('select-rank/', views.UserRankListView.as_view(), name='select_rank'), #ユーザーのリスト表示
    path('user-list/', views.UserListView.as_view(), name='user_list'), #ユーザーのリスト表示
    path('constant-list/', views.ConstantListView.as_view(), name='constant_list'), #定数のリストを表示
    path('constant-update/', views.ConstantUpdateView.as_view(), name='constant_update'), #定数を編集
]
