import functools
import string
import time
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from GutenReaderApp.models import Book, SubjectTag
from django.views import View
from django.http import Http404
from haystack.query import SearchQuerySet

MAX_PAGE_ITEMS = 100  # number of items (books or tags) shown on 1 page(shelf, subject_tags, search)
NUM_TOP_BOOKS_HOME = 10  # top <int> books shown on home page


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)  # Call the original function
        end_time = time.time()
        time_taken = end_time - start_time

        # Check if the first argument is an instance of a class
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__
            print(f"{class_name}'s {func.__name__} took {time_taken:.3f} seconds to execute.")
        else:
            print(f"{func.__name__} took {time_taken:.3f} seconds to execute.")

        return result  # Return the result of the original function

    return wrapper


def get_books_order_by(order_by='-view_count', max_items=MAX_PAGE_ITEMS):
    # Try to get data from the cache
    book_models = None
    if max_items <= MAX_PAGE_ITEMS:
        book_models = cache.get('top_book_models')
    if book_models is None:
        book_models = cache.get('book_models')
        if book_models is not None:
            cache.set('top_book_models', book_models[:max_items], None)
    if book_models is None:
        # If not in cache, query the database and cache the result
        book_models = cache_book_models(max_items)
    book_models = book_models[:max_items]
    return book_models


def cache_book_models(max_items=MAX_PAGE_ITEMS):
    book_models = []
    book_tuple_list = []
    last_pk = Book.objects.last().pk
    for pk in range(1, last_pk + 1):
        try:
            book = Book.objects.get(pk=pk)
        except Exception as e:
            continue
        book_tuple_list.append((book.pk, book.view_count))
    book_tuple_list = sorted(book_tuple_list, key=lambda x: -1 * x[1])
    for book_tuple in book_tuple_list[:max_items]:
        book_models.append(Book.objects.get(pk=book_tuple[0]))
    cache.set('book_models', book_models, None)
    cache.set('top_book_models', book_models[:MAX_PAGE_ITEMS], None)
    return book_models


def get_tags_order_by(order_by='-num_books', max_items=MAX_PAGE_ITEMS):
    # Try to get data from the cache
    subject_tag_data = None
    if max_items <= MAX_PAGE_ITEMS:
        subject_tag_data = cache.get('top_subject_tag_data')
    if subject_tag_data is None:
        subject_tag_data = cache.get('subject_tag_data')
        if subject_tag_data is not None:
            cache.set('top_subject_tag_data', subject_tag_data[:max_items], None)
    if subject_tag_data is None:
        # If not in cache, query the database and cache the result
        subject_tag_data = cache_subject_tag_models(max_items)
    subject_tag_data = subject_tag_data[:max_items]

    return subject_tag_data


def cache_subject_tag_models(max_items=MAX_PAGE_ITEMS):
    tag_models = []
    tag_tuple_list = []
    last_pk = SubjectTag.objects.last().pk
    for pk in range(1, last_pk + 1):
        try:
            tag = SubjectTag.objects.get(pk=pk)
        except Exception as e:
            continue
        tag_tuple_list.append((tag.pk, tag.num_books))
    tag_tuple_list = sorted(tag_tuple_list, key=lambda x: -1 * x[1])
    for tag_tuple in tag_tuple_list[:max_items]:
        tag_models.append(SubjectTag.objects.get(pk=tag_tuple[0]))
    content_and_book_count = []
    for tag in tag_models:
        if tag.num_books == 1:
            content_and_book_count.append((tag.books.all()[0], tag.content, tag.num_books))
        else:
            content_and_book_count.append((tag, tag.content, tag.num_books))
    subject_tag_data = content_and_book_count
    cache.set('subject_tag_data', subject_tag_data, None)
    cache.set('top_subject_tag_data', subject_tag_data[:MAX_PAGE_ITEMS], None)
    return subject_tag_data


def get_home_books(max_items=NUM_TOP_BOOKS_HOME):
    # Try to get data from the cache
    home_page_books = cache.get('home_page_books')
    if home_page_books is None:
        # If not in cache, query the database and cache the result
        top_x_books = get_books_order_by(max_items=max_items)
        home_page_books = []
        for book in top_x_books:
            subject_tags = SubjectTag.objects.filter(books=book)
            tag_list = []
            for tag in subject_tags:
                tag_list.append(tag)
            home_page_books.append((book, get_cover_url(book), tag_list))
        cache.set('home_page_books', home_page_books, None)
    return home_page_books


def get_cover_url(current_book: Book):
    cover_url = ""
    try:
        cover_url = current_book.book_cover.url
    except Exception as e:  # should be value error
        cover_url = "/media/book_covers/default_cover.png"  # default cover path
    return cover_url


# Create your views here.
class Home(View):
    @timeit
    def get(self, request):
        home_page_books = get_home_books()
        return render(request, "home.html",
                      {"Title": "GutenReader",
                       'Book_list': home_page_books})


class Shelf(View):  # all books
    @timeit
    def get(self, request):
        books = get_books_order_by(max_items=100)
        return render(request, "shelf.html",
                      {"books": books, "page_header": "Books", "Title": "Books - GutenReader"})


class About(View):
    @timeit
    def get(self, request):
        return render(request, "about.html",
                      {"Title": "About - GutenReader"})


class Search(View):
    @timeit
    def post(self, request):
        user_query: string = request.POST['search']
        if user_query.startswith('by:'):  # search by author
            user_query = user_query[3:].strip()
            filtered_books = SearchQuerySet().models(Book).filter(author=user_query)
            ordered_filtered_books = []
            for book in filtered_books:
                ordered_filtered_books.append(Book.objects.get(pk=book.pk))
            return render(request,
                          "shelf.html",  # uses existing shelf template
                          {"books": ordered_filtered_books[:MAX_PAGE_ITEMS],
                           "page_header": f"Books by \"{user_query}\"",
                           "Title": ("Search: " + user_query)})
        elif user_query.startswith('tag:'):  # search by tag
            user_query = user_query[4:].strip()
            filtered_tags = SearchQuerySet().models(SubjectTag).filter(content=user_query)
            ordered_filtered_tags = list(filtered_tags)
            content_and_book_count = []
            for tag in ordered_filtered_tags:
                tag_model = (SubjectTag.objects.get(pk=tag.pk))
                content_and_book_count.append((tag_model, tag.content, tag.num_books))
            return render(request,
                          "subject_tags.html",  # uses existing subject_tags template
                          {'tags': content_and_book_count[:MAX_PAGE_ITEMS],
                           "page_header": f"\"{user_query}\" Tags",
                           'Title': ("Search: " + user_query)})
        else:  # search by title
            filtered_books = SearchQuerySet().models(Book).filter(title=user_query)
            ordered_filtered_books = []
            for book in filtered_books:
                ordered_filtered_books.append(Book.objects.get(pk=book.pk))
            return render(request,
                          "shelf.html",  # uses existing shelf template
                          {"books": ordered_filtered_books[:MAX_PAGE_ITEMS],
                           "page_header": f"\"{user_query}\" Books",
                           "Title": ("Search: " + user_query)})


class Index(View):  # book_index
    @timeit
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


class Chapter(View):  # a single book chapter
    @timeit
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


class SubjectTags(View):  # all subject tags
    @timeit
    def get(self, request):
        content_and_book_count = get_tags_order_by()
        context = {'tags': content_and_book_count[:MAX_PAGE_ITEMS],
                   "page_header": "Subject Tags",
                   'Title': "Subject Tags - GutenReader"
                   }
        return render(request, "subject_tags.html", context)


class TagIndex(View):  # list of all books with a particular tag
    @timeit
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
