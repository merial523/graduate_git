from django.shortcuts import render,redirect


def index(request):

        if request.user.rank == "administer":
            return render(request,"administer/administer_index.html")
        elif request.user.rank == "moderator":
            return render(request,"moderator/moderator_index.html")
        elif request.user.rank == "staff":
            return render(request,"staff/staff_index.html")
        elif request.user.rank == "visitor":
            return render(request,"visitor/visitor_index.html")
        else:
            return render(request, "main/a.html")


