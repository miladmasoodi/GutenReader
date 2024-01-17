from django.shortcuts import render, redirect
from models import Book
from django.views import View


# Create your views here.
class Home(View):
    def get(self, request):
        books = list(Book.objects.all())
        return render(request, "home.html", {"books": books})
