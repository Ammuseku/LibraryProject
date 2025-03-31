from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Book, Student, Pupil


class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'isbn', 'year', 'quantity', 'label', 'borrower_count', 'view_borrowers')
    list_filter = ('label', 'year')
    search_fields = ('title', 'author', 'isbn')

    def borrower_count(self, obj):
        """Count how many users have borrowed this book."""
        student_count = obj.borrowed_by_students.count()
        pupil_count = obj.borrowed_by_pupils.count()
        return f"{student_count + pupil_count} ({student_count} students, {pupil_count} pupils)"

    borrower_count.short_description = 'Borrowers'

    def view_borrowers(self, obj):
        """Link to view borrowers in the front-end."""
        url = reverse('borrowed_books') + f'?book_id={obj.id}'
        return format_html('<a href="{}" class="button">View Borrowers</a>', url)

    view_borrowers.short_description = 'Actions'

    actions = ['mark_as_unavailable', 'mark_as_available']

    def mark_as_unavailable(self, request, queryset):
        """Mark selected books as unavailable (quantity=0)."""
        updated = queryset.update(quantity=0)
        self.message_user(request, f"{updated} books marked as unavailable.")

    mark_as_unavailable.short_description = "Mark selected books as unavailable"

    def mark_as_available(self, request, queryset):
        """Mark selected books as available with 1 copy."""
        updated = queryset.update(quantity=1)
        self.message_user(request, f"{updated} books marked as available (quantity=1).")

    mark_as_available.short_description = "Mark selected books as available (quantity=1)"


class BorrowedBooksInline(admin.TabularInline):
    model = Student.borrowed_books.through
    extra = 1
    verbose_name = "Borrowed Book"
    verbose_name_plural = "Borrowed Books"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "book":
            kwargs["queryset"] = Book.objects.filter(quantity__gt=0)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'surname', 'group', 'borrowed_book_count', 'view_books')
    search_fields = ('user_id', 'name', 'surname', 'group')
    list_filter = ('group',)
    exclude = ('borrowed_books',)
    inlines = [BorrowedBooksInline]

    def borrowed_book_count(self, obj):
        """Count how many books this student has borrowed."""
        return obj.borrowed_books.count()

    borrowed_book_count.short_description = 'Books Borrowed'

    def view_books(self, obj):
        """Link to view borrowed books in the front-end."""
        url = reverse('user_books', kwargs={'user_type': 'student', 'user_id': obj.user_id})
        return format_html('<a href="{}" class="button">View Books</a>', url)

    view_books.short_description = 'Actions'

    actions = ['return_all_books']

    def return_all_books(self, request, queryset):
        """Return all books borrowed by selected students."""
        total_returned = 0
        for student in queryset:
            books = list(student.borrowed_books.all())
            for book in books:
                book.quantity += 1
                book.save()
                student.borrowed_books.remove(book)
                total_returned += 1

        self.message_user(request, f"{total_returned} books returned from {queryset.count()} students.")

    return_all_books.short_description = "Return all books from selected students"


class PupilBorrowedBooksInline(admin.TabularInline):
    model = Pupil.borrowed_books.through
    extra = 1
    verbose_name = "Borrowed Book"
    verbose_name_plural = "Borrowed Books"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "book":
            kwargs["queryset"] = Book.objects.filter(quantity__gt=0, label='for children')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PupilAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'surname', 'group', 'age', 'borrowed_book_count', 'view_books')
    search_fields = ('user_id', 'name', 'surname', 'group')
    list_filter = ('group', 'age')
    exclude = ('borrowed_books',)
    inlines = [PupilBorrowedBooksInline]

    def borrowed_book_count(self, obj):
        """Count how many books this pupil has borrowed."""
        return obj.borrowed_books.count()

    borrowed_book_count.short_description = 'Books Borrowed'

    def view_books(self, obj):
        """Link to view borrowed books in the front-end."""
        url = reverse('user_books', kwargs={'user_type': 'pupil', 'user_id': obj.user_id})
        return format_html('<a href="{}" class="button">View Books</a>', url)

    view_books.short_description = 'Actions'

    actions = ['return_all_books']

    def return_all_books(self, request, queryset):
        """Return all books borrowed by selected pupils."""
        total_returned = 0
        for pupil in queryset:
            books = list(pupil.borrowed_books.all())
            for book in books:
                book.quantity += 1
                book.save()
                pupil.borrowed_books.remove(book)
                total_returned += 1

        self.message_user(request, f"{total_returned} books returned from {queryset.count()} pupils.")

    return_all_books.short_description = "Return all books from selected pupils"


# Register models with custom admin classes
admin.site.register(Book, BookAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Pupil, PupilAdmin)