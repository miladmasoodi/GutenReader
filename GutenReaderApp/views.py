import string

from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from GutenReaderApp.models import Book, SubjectTag
from django.views import View
from django.http import Http404


MAX_PAGE_ITEMS = 300
def get_cover_url(current_book: Book):
    cover_url = ""
    try:
        cover_url = current_book.book_cover.url
    except Exception as e:  # should be value error
        cover_url = "/media/book_covers/default_cover.png"
    return cover_url

# Create your views here.
class Home(View):
    def get(self, request):
        top_5_books = list(Book.objects.order_by("-view_count").all())[:5]
        book_list = []
        for book in top_5_books:
            subject_tags = SubjectTag.objects.filter(books=book)
            tag_list = []
            for tag in subject_tags:
                tag_list.append(tag)

            book_list.append((book, get_cover_url(book), tag_list))

        return render(request, "home.html",
                      {"Title": "GutenReader",
                                'Book_list': book_list})
class Shelf(View):
    def get(self, request):
        books = list(Book.objects.order_by("-view_count").all())  # "-" at start makes it descending order
        return render(request, "shelf.html",
                      {"books": books, "page_header": "Books", "Title": "Books - GutenReader"})

class About(View):
    def get(self, request):
        books = list(Book.objects.order_by("-view_count").all())  # "-" at start makes it descending order
        return render(request, "about.html",
                      {"Title": "About - GutenReader"})
class Search(View):
    def post(self, request):
        user_query: string = request.POST['search']
        if user_query.startswith('by:'):  # search by author
            user_query = user_query[3:].strip()
            filtered_books = Book.objects.filter(author__icontains=user_query)
            ordered_filtered_books = list(filtered_books.order_by("-view_count").all())
            return render(request,
                          "shelf.html",
                          {"books": ordered_filtered_books[:MAX_PAGE_ITEMS],
                           "page_header": f"Books by \"{user_query}\"",
                           "Title": ("Search: " + user_query)})
        elif user_query.startswith('tag:'):  # search by tag
            user_query = user_query[4:].strip()
            filtered_tags = SubjectTag.objects.filter(content__icontains=user_query)
            ordered_filtered_tags = list(filtered_tags.annotate(num_books=Count("books")).order_by('-num_books'))
            content_and_book_count = []
            for tag in ordered_filtered_tags:
                number_of_books = tag.num_books
                if number_of_books == 1:
                    content_and_book_count.append((tag.books.all()[0], tag.content, number_of_books))
                else:
                    content_and_book_count.append((tag, tag.content, number_of_books))
            return render(request,
                          "subject_tags.html",
                          {'tags': content_and_book_count[:MAX_PAGE_ITEMS],
                           "page_header": f"\"{user_query}\" Tags",
                           'Title': ("Search: " + user_query)})
        else:  # search by title
            filtered_books = Book.objects.filter(title__icontains=user_query)
            ordered_filtered_books = list(filtered_books.order_by("-view_count").all())
            return render(request,
                          "shelf.html",
                          {"books": ordered_filtered_books[:MAX_PAGE_ITEMS],
                           "page_header": f"\"{user_query}\" Books",
                           "Title": ("Search: " + user_query)})


class Index(View):
    def get(self, request, book_id):
        current_book = get_object_or_404(Book, pk=book_id)
        subject_tags = SubjectTag.objects.filter(books=current_book)
        tag_list = []
        for tag in subject_tags:
            tag_list.append(tag)
        chap_titles = []
        section_count = 0
        for i in range(len(current_book.chapter_titles)):
            if len(current_book.section_indices) > section_count and current_book.section_indices[section_count] == i:
                section_count += 1
                chap_titles.append((current_book.chapter_titles[i], -1))
            else:  # not 0 based since user-facing
                chap_titles.append((current_book.chapter_titles[i], i - section_count + 1))
        cover_url = get_cover_url(current_book)

        context = {'Book': current_book,
                   "HasTranslator": current_book.translater != '',
                   'Chap_Titles': chap_titles,
                   'tag_list': tag_list,
                   'cover_url': cover_url,
                   'Title': current_book.title + " - GutenReader",
                   }
        return render(request, "book_index.html", context)


class Chapter(View):
    def get(self, request, book_id, chapter_id):
        current_book = get_object_or_404(Book, pk=book_id)

        viewed_books = request.session.get("viewed_books", [])
        if book_id not in viewed_books:
            viewed_books.append(book_id)
            request.session["viewed_books"] = viewed_books
            current_book.view_count = current_book.view_count + 1
            current_book.save()

        max_chapters = len(current_book.chapter_divisions) - len(current_book.section_indices) - 1
        sections_before = 0
        # adjusted_chap_id is for the book model, chapter_id is for front-end
        adjusted_chap_id = chapter_id
        for index_value in current_book.section_indices:
            if index_value < adjusted_chap_id:
                sections_before += 1
                adjusted_chap_id += 1

        if chapter_id > max_chapters or chapter_id < 1:
            raise Http404(f'No such chapter: {chapter_id}')
        chapter_start = current_book.chapter_divisions[adjusted_chap_id - 1]
        chapter_end = current_book.chapter_divisions[adjusted_chap_id]
        content = '\n'.join(current_book.full_text.splitlines()[chapter_start:chapter_end])
        has_next_chapter = chapter_id < max_chapters
        has_prev_chapter = chapter_id > 1
        title = current_book.title + " Ch: " + current_book.chapter_titles[adjusted_chap_id - 1]

        context = {'book': current_book,
                   'Chap_Title': current_book.chapter_titles[adjusted_chap_id - 1],
                   'Content': content,
                   'chapter_id': chapter_id,
                   'chapter_id_prev': chapter_id - 1,
                   'chapter_id_next': chapter_id + 1,
                   'has_next_chapter': has_next_chapter,
                   'has_prev_chapter': has_prev_chapter,
                   'Title': title + " - GutenReader",
                   }
        return render(request, "chapter.html", context)


class SubjectTags(View):
    def get(self, request):
        tags = list(SubjectTag.objects.annotate(num_books=Count("books")).order_by('-num_books').all())
        content_and_book_count = []
        for tag in tags:
            number_of_books = tag.num_books
            if number_of_books == 1:
                content_and_book_count.append((tag.books.all()[0], tag.content, number_of_books))
            else:
                content_and_book_count.append((tag, tag.content, number_of_books))

        context = {'tags': content_and_book_count[:MAX_PAGE_ITEMS],
                   "page_header": "Subject Tags",
                   'Title': "Subject Tags - GutenReader"
                   }
        return render(request, "subject_tags.html", context)


class TagIndex(View):
    def get(self, request, tag_id):
        current_tag = get_object_or_404(SubjectTag, pk=tag_id)
        books = current_tag.books.all()
        number_of_books = len(books)
        if number_of_books == 1:  # if only 1 book: redirect to that book
            redirect(list(books)[0])
        ordered_books = list(books.order_by("-view_count").all())
        context = {'books': ordered_books,
                   'Title': f"Subject: {current_tag.content} - GutenReader",
                   'tag': current_tag
                   }
        return render(request, "tag_index.html", context)
