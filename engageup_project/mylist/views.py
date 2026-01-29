from django.shortcuts import render


# Create your views here.
def mylist_index(request):
    return render(request, "mylist/4101.html")

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from main.models import News,Mylist

@login_required
def add_favorite_news(request, news_id):
    news = get_object_or_404(News, id=news_id)

    Mylist.objects.get_or_create(
        user=request.user,
        news=news
    )

    return redirect("news_detail", news_id=news.id)

@login_required
def remove_favorite_news(request, news_id):
    Mylist.objects.filter(
        user=request.user,
        news_id=news_id
    ).delete()

    return redirect("news_detail", news_id=news_id)
