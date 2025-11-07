from django.shortcuts import render

# Create your views here.
# Create your views here.
def accounts_index(request):
    return render(request, "accounts/accountsIndex.html")
