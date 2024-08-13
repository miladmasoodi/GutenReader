from haystack import indexes
from .models import Book, SubjectTag

class BookIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    author = indexes.CharField(model_attr='author')
    pid = indexes.IntegerField(model_attr='pk')


    def get_model(self):
        return Book

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class SubjectTagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    content = indexes.CharField(model_attr='content')
    pid = indexes.IntegerField(model_attr='pk')
    num_books = indexes.IntegerField(model_attr='num_books')



    def get_model(self):
        return SubjectTag

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
