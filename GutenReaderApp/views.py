from django.shortcuts import render, redirect
from GutenReaderApp.models import Book
from django.views import View


# Create your views here.
class Home(View):
    def get(self, request):
        books = list(Book.objects.all())
        return render(request, "home.html", {"books": books})
class Index(View):
    def get(self, request, book_id):
        current_book = Book.objects.get(id=book_id)

