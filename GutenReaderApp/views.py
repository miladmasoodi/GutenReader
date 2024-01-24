from django.shortcuts import render, redirect, get_object_or_404
from GutenReaderApp.models import Book
from django.views import View


# Create your views here.
class Home(View):
    def get(self, request):
        books = list(Book.objects.all())
        return render(request, "home.html", {"books": books})
class Index(View):
    def get(self, request, book_id):
        current_book = get_object_or_404(Book, pk=book_id)

        context = {'Title': current_book.Title, 'Author': current_book.Author, 'Language': current_book.Language,
                   'Chap_Titles': current_book.chapter_titles}
        return render(request, "bookIndex.html", context)
