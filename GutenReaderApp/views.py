from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from GutenReaderApp.models import Book, SubjectTag
from django.views import View
from django.http import Http404


# Create your views here.
class Home(View):
    def get(self, request):
        books = list(Book.objects.order_by("-view_count").all())  # "-" at start makes it descending order
        return render(request, "home.html", {"books": books, "Title": "Home - GutenReader"})


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
        cover_url = ""
        try:
            cover_url = current_book.book_cover.url
        except Exception as e:  # should be value error
            cover_url = "/media/book_covers/default_cover.png"

        context = {'Book': current_book,
                   "HasTranslator": current_book.translater != '',
                   'Chap_Titles': chap_titles,
                   'tag_list': tag_list,
                   'cover_url': cover_url
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
                   'Title': title,
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

        context = {'tags': content_and_book_count,
                   'Title': "Subject Tags"
                   }
        return render(request, "subject_tags.html", context)

class TagIndex(View):
    def get(self, request, tag_id):
        current_tag = get_object_or_404(SubjectTag, pk=tag_id)
        books = current_tag.books.all()
        number_of_books = len(books)
        if number_of_books == 1:  # auto-redirect to only book, of only 1 book
            redirect(list(books)[0])
        ordered_books = list(books.order_by("-view_count").all())
        context = {'books': ordered_books,
                   'Title': f"Subject: {current_tag.content}",
                   'tag': current_tag
                   }
        return render(request, "tag_index.html", context)




