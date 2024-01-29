from django.shortcuts import render, redirect, get_object_or_404
from GutenReaderApp.models import Book
from django.views import View
from django.http import Http404


# Create your views here.
class Home(View):
    def get(self, request):
        books = list(Book.objects.all())
        return render(request, "home.html", {"books": books})


class Index(View):
    def get(self, request, book_id):
        current_book = get_object_or_404(Book, pk=book_id)
        chap_titles = []
        for i in range(len(current_book.chapter_titles)):
            chap_titles.append((current_book.chapter_titles[i], i+1))  # not 0 based since user-facing

        context = {'Title': current_book.title, 'Author': current_book.author, 'Language': current_book.language,
                   'Chap_Titles': chap_titles, 'book_id': current_book.pk}
        return render(request, "book_index.html", context)

class Chapter(View):
    def get(self, request, book_id, chapter_id):
        current_book = get_object_or_404(Book, pk=book_id)
        max_chapters = len(current_book.chapter_divisions)-1
        if chapter_id > max_chapters or chapter_id < 1:
            raise Http404(f'No such chapter: {chapter_id}')
        chapter_start = current_book.chapter_divisions[chapter_id-1]
        chapter_end = current_book.chapter_divisions[chapter_id]
        content = current_book.full_text[chapter_start:chapter_end]

        context = {'Book_Title': current_book.title,
                   'Chap_Title': current_book.chapter_titles[chapter_id-1],
                   'Content': content,
                   'book_id': current_book.pk,
                   'chapter_id': chapter_id,
                   'chapter_id_prev': chapter_id-1,  # needs checks and disabling for button
                   'chapter_id_next': chapter_id+1
                   }
        return render(request, "chapter.html", context)
