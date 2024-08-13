"""
URL configuration for GutenReaderProject project.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from GutenReaderApp.views import Home, Index, Chapter, SubjectTags, TagIndex, Search, Shelf, About

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Home.as_view(), name='home'),
    path('about', About.as_view(), name='about'),
    path('search', Search.as_view(), name='search'),
    path('books', Shelf.as_view(), name='shelf'),
    path('books/<int:book_id>/', Index.as_view(), name='index'),
    path('books/<int:book_id>/<int:chapter_id>', Chapter.as_view(), name='chapter'),
    path('subject-tags/', SubjectTags.as_view(), name='subject-tags'),
    path('subject-tags/<int:tag_id>', TagIndex.as_view(), name='tag-index'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # needs testing
