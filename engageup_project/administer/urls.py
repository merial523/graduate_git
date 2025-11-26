from django.urls import path
from . import views

urlpatterns = [
    path('administer/', views.administer_index, name = "administer_index"),
    path('select-rank/', views.select_rank, name='select_rank'),
]
