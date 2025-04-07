# library/admin.py (with borrowing and returning operations)
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django import forms
from .models import Book, Student, Pupil
from .library import Library


# Custom Forms for Borrowing/Returning in Admin
class BorrowBookForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(quantity__gt=0),
        label="Select Book to Borrow",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ReturnBookForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        label="Select Book to Return",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super(ReturnBookForm, self).__init__(*args, **kwargs)
        if user:
            # Only show books borrowed by this user
            self.fields['book'].queryset = user.borrowed_books.all()


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
    list_display = ('user_id', 'name', 'surname', 'group', 'borrowed_book_count', 'view_books', 'admin_actions')
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

    view_books.short_description = 'View Books'

    def admin_actions(self, obj):
        """Link to borrow/return books in admin."""
        borrow_url = reverse('admin:borrow_book', args=[obj.pk, 'student'])
        return_url = reverse('admin:return_book', args=[obj.pk, 'student'])

        return format_html(
            '<a href="{}" class="button">Borrow Book</a> '
            '<a href="{}" class="button">Return Book</a>',
            borrow_url, return_url
        )

    admin_actions.short_description = 'Book Operations'

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

    # Custom admin views for borrowing and returning books
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('borrow-book/<int:user_id>/<str:user_type>/',
                 self.admin_site.admin_view(self.borrow_book_view),
                 name='borrow_book'),
            path('return-book/<int:user_id>/<str:user_type>/',
                 self.admin_site.admin_view(self.return_book_view),
                 name='return_book'),
        ]
        return custom_urls + urls

    def borrow_book_view(self, request, user_id, user_type):
        # Get the user object
        if user_type == 'student':
            user = Student.objects.get(pk=user_id)
        else:  # pupil
            user = Pupil.objects.get(pk=user_id)

        # Initialize form
        if user_type == 'student':
            form = BorrowBookForm()  # Students can borrow any available book
        else:  # pupil
            # Pupils can only borrow children's books
            form = BorrowBookForm()
            form.fields['book'].queryset = Book.objects.filter(
                quantity__gt=0,
                label='for children'
            )

        if request.method == 'POST':
            if user_type == 'student':
                form = BorrowBookForm(request.POST)
            else:  # pupil
                form = BorrowBookForm(request.POST)
                form.fields['book'].queryset = Book.objects.filter(
                    quantity__gt=0,
                    label='for children'
                )

            if form.is_valid():
                book = form.cleaned_data['book']

                # Use the Library service to handle the borrowing logic
                success, message = Library.process_borrowing(user, book)

                if success:
                    self.message_user(request, message, messages.SUCCESS)
                else:
                    self.message_user(request, message, messages.ERROR)

                # Redirect back to the user's admin page
                if user_type == 'student':
                    return HttpResponseRedirect(
                        reverse('admin:library_student_change', args=[user_id])
                    )
                else:  # pupil
                    return HttpResponseRedirect(
                        reverse('admin:library_pupil_change', args=[user_id])
                    )

        # Render the form template
        context = {
            'form': form,
            'user': user,
            'user_type': user_type,
            'title': f'Borrow Book for {user.name} {user.surname}',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/library/borrow_book.html', context)

    def return_book_view(self, request, user_id, user_type):
        # Get the user object
        if user_type == 'student':
            user = Student.objects.get(pk=user_id)
        else:  # pupil
            user = Pupil.objects.get(pk=user_id)

        # Initialize form with only the books this user has borrowed
        form = ReturnBookForm(user=user)

        if request.method == 'POST':
            form = ReturnBookForm(user=user, data=request.POST)

            if form.is_valid():
                book = form.cleaned_data['book']

                # Use the Library service to handle the returning logic
                success, message = Library.process_return(user, book)

                if success:
                    self.message_user(request, message, messages.SUCCESS)
                else:
                    self.message_user(request, message, messages.ERROR)

                # Redirect back to the user's admin page
                if user_type == 'student':
                    return HttpResponseRedirect(
                        reverse('admin:library_student_change', args=[user_id])
                    )
                else:  # pupil
                    return HttpResponseRedirect(
                        reverse('admin:library_pupil_change', args=[user_id])
                    )

        # Render the form template
        context = {
            'form': form,
            'user': user,
            'user_type': user_type,
            'title': f'Return Book for {user.name} {user.surname}',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/library/return_book.html', context)


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
    list_display = ('user_id', 'name', 'surname', 'group', 'age', 'borrowed_book_count', 'view_books', 'admin_actions')
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

    view_books.short_description = 'View Books'

    def admin_actions(self, obj):
        """Link to borrow/return books in admin."""
        borrow_url = reverse('admin:borrow_book', args=[obj.pk, 'pupil'])
        return_url = reverse('admin:return_book', args=[obj.pk, 'pupil'])

        return format_html(
            '<a href="{}" class="button">Borrow Book</a> '
            '<a href="{}" class="button">Return Book</a>',
            borrow_url, return_url
        )

    admin_actions.short_description = 'Book Operations'

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

    # Pupil admin will reuse the custom admin views from StudentAdmin
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        student_admin = StudentAdmin(Student, self.admin_site)
        custom_urls = [
            path('borrow-book/<int:user_id>/<str:user_type>/',
                 self.admin_site.admin_view(student_admin.borrow_book_view),
                 name='borrow_book'),
            path('return-book/<int:user_id>/<str:user_type>/',
                 self.admin_site.admin_view(student_admin.return_book_view),
                 name='return_book'),
        ]
        return custom_urls + urls


# Register models with custom admin classes
admin.site.register(Book, BookAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Pupil, PupilAdmin)