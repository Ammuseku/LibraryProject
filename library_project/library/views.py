# library/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Book, Student, Pupil
from .forms import BookForm, StudentForm, PupilForm, BorrowForm, ReturnForm, UserTypeCheckForm
from .library import Library


def home(request):
    return render(request, 'library/home.html')


def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})


def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully.')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/add_book.html', {'form': form})


def user_list(request):
    students = Student.objects.all()
    pupils = Pupil.objects.all()
    return render(request, 'library/user_list.html', {'students': students, 'pupils': pupils})


def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                student = form.save()
                messages.success(request, 'Student added successfully.')
                return redirect('user_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = StudentForm()
    return render(request, 'library/add_student.html', {'form': form})


def add_pupil(request):
    if request.method == 'POST':
        form = PupilForm(request.POST)
        if form.is_valid():
            try:
                pupil = form.save()
                messages.success(request, 'Pupil added successfully.')
                return redirect('user_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = PupilForm()
    return render(request, 'library/add_pupil.html', {'form': form})


def borrow_book(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            user_id = form.cleaned_data['user_id']
            book_id = form.cleaned_data['book_id']

            try:
                book = get_object_or_404(Book, id=book_id)

                if user_type == 'student':
                    user = get_object_or_404(Student, user_id=user_id)
                else:  # pupil
                    user = get_object_or_404(Pupil, user_id=user_id)

                success, message = Library.process_borrowing(user, book)
                if success:
                    messages.success(request, message)
                    return redirect('user_list')
                else:
                    messages.error(request, message)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = BorrowForm()

    return render(request, 'library/borrow_book.html', {'form': form})


def return_book(request):
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            user_id = form.cleaned_data['user_id']
            book_id = form.cleaned_data['book_id']

            try:
                book = get_object_or_404(Book, id=book_id)

                if user_type == 'student':
                    user = get_object_or_404(Student, user_id=user_id)
                else:  # pupil
                    user = get_object_or_404(Pupil, user_id=user_id)

                success, message = Library.process_return(user, book)
                if success:
                    messages.success(request, message)
                    return redirect('user_list')
                else:
                    messages.error(request, message)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ReturnForm()

    return render(request, 'library/return_book.html', {'form': form})


def check_user_type(request):
    if request.method == 'POST':
        form = UserTypeCheckForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            try:
                user_type = Library.get_user_type(user_id)
                messages.info(request, f"ID {user_id} belongs to a {user_type}.")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = UserTypeCheckForm()

    return render(request, 'library/check_user_type.html', {'form': form})


def user_books(request, user_type, user_id):
    if user_type == 'student':
        user = get_object_or_404(Student, user_id=user_id)
    else:  # pupil
        user = get_object_or_404(Pupil, user_id=user_id)

    borrowed_books = user.borrowed_books.all()
    return render(request, 'library/user_books.html', {
        'user': user,
        'borrowed_books': borrowed_books
    })