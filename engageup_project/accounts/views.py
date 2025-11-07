from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # ログインページへリダイレクト
    else:
        form = UserCreationForm()
    return render(request, 'accounts/1102.html', {'form': form})