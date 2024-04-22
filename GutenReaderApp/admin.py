from django.contrib import admin
from GutenReaderApp.models import Book, TextUpload, SubjectTag
# Register your models here.
admin.site.register(Book)
admin.site.register(TextUpload)
admin.site.register(SubjectTag)
