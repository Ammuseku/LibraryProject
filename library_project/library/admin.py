# library/admin.py
from django.contrib import admin
from .models import Book, Student, Pupil

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'year', 'quantity', 'label')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('label',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'surname', 'group')
    search_fields = ('user_id', 'name', 'surname')
    filter_horizontal = ('borrowed_books',)

@admin.register(Pupil)
class PupilAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'surname', 'group', 'age')
    search_fields = ('user_id', 'name', 'surname')
    list_filter = ('age',)
    filter_horizontal = ('borrowed_books',)