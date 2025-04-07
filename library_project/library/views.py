# library/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Book, Student, Pupil
from .forms import BookForm, StudentForm, PupilForm, BorrowForm, ReturnForm, UserTypeCheckForm
from .library import Library


import pickle
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages



# Text File Operations
def export_books_txt(request):
    """Export books to a text file (books.txt)"""
    books = Book.objects.all()

    # Create text content
    content = ""
    for book in books:
        content += f"{book.title},{book.label}\n"

    # Create response with file
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="books.txt"'

    messages.success(request, f"Successfully exported {books.count()} books to books.txt")
    return response


def import_books_txt(request):
    """Import books from a text file"""
    if request.method == 'POST' and request.FILES.get('books_file'):
        books_file = request.FILES['books_file']

        # Read and process the file
        lines = books_file.read().decode('utf-8').splitlines()

        books_created = 0
        for line in lines:
            if not line.strip():  # Skip empty lines
                continue

            try:
                # Parse line format: title,label
                parts = line.split(',')
                if len(parts) >= 2:
                    title = parts[0].strip()
                    label = parts[1].strip()

                    # Make sure label is valid
                    if label not in ['for children', 'general']:
                        label = 'general'  # Default to general if invalid

                    # Create a new book
                    book = Book(
                        title=title,
                        author="Imported Author",  # Default author
                        isbn=f"IMP{books_created:06d}",  # Generate a unique ISBN
                        year=2023,  # Default year
                        quantity=1,  # Default quantity
                        label=label
                    )
                    book.save()
                    books_created += 1
            except Exception as e:
                # Log the error but continue processing
                print(f"Error importing line: {line}. Error: {str(e)}")

        messages.success(request, f"Successfully imported {books_created} books.")
        return redirect('book_list')

    return render(request, 'library/import_books.html')


# Binary File Operations (Serialization)
def serialize_library(request):
    """Serialize all library data to a pickle file"""
    # Get all data
    books = list(Book.objects.all())
    students = list(Student.objects.all())
    pupils = list(Pupil.objects.all())

    # Serialize data
    library_data = {
        'books': books,
        'students': students,
        'pupils': pupils
    }

    # Create pickle file
    serialized_data = pickle.dumps(library_data)

    # Create response with file
    response = HttpResponse(serialized_data, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename="library.pkl"'

    messages.success(request, "Library data serialized and downloaded successfully")
    return response


def deserialize_library(request):
    """Deserialize library data from a pickle file"""
    if request.method == 'POST' and request.FILES.get('library_file'):
        try:
            # Read pickle file
            library_file = request.FILES['library_file']
            library_data = pickle.loads(library_file.read())

            # Check if we got valid data
            if not isinstance(library_data, dict) or not all(
                    k in library_data for k in ['books', 'students', 'pupils']):
                messages.error(request, "Invalid library data file format")
                return redirect('home')

            # Clear existing data if option is selected
            if request.POST.get('clear_existing') == 'yes':
                drop_all_data(request, silent=True)

            # Import books
            books_count = 0
            for book_obj in library_data['books']:
                try:
                    # Check if this book already exists
                    existing_book = Book.objects.filter(isbn=book_obj.isbn).first()
                    if existing_book:
                        # Update existing book
                        existing_book.title = book_obj.title
                        existing_book.author = book_obj.author
                        existing_book.year = book_obj.year
                        existing_book.quantity = book_obj.quantity
                        existing_book.label = book_obj.label
                        existing_book.save()
                    else:
                        # Create new book
                        book = Book(
                            title=book_obj.title,
                            author=book_obj.author,
                            isbn=book_obj.isbn,
                            year=book_obj.year,
                            quantity=book_obj.quantity,
                            label=book_obj.label
                        )
                        book.save()
                    books_count += 1
                except Exception as e:
                    print(f"Error importing book: {str(e)}")

            # Import students
            students_count = 0
            for student_obj in library_data['students']:
                try:
                    # Check if this student already exists
                    existing_student = Student.objects.filter(user_id=student_obj.user_id).first()
                    if existing_student:
                        # Update existing student
                        existing_student.name = student_obj.name
                        existing_student.surname = student_obj.surname
                        existing_student.group = student_obj.group
                        existing_student.save()
                    else:
                        # Create new student
                        student = Student(
                            user_id=student_obj.user_id,
                            name=student_obj.name,
                            surname=student_obj.surname,
                            group=student_obj.group
                        )
                        student.save()
                    students_count += 1

                    # Handle borrowed books
                    if existing_student:
                        student = existing_student
                    else:
                        student = Student.objects.get(user_id=student_obj.user_id)

                    # Clear existing borrowed books
                    student.borrowed_books.clear()

                    # Add borrowed books
                    for book in student_obj.borrowed_books.all():
                        try:
                            db_book = Book.objects.get(isbn=book.isbn)
                            student.borrowed_books.add(db_book)
                        except Book.DoesNotExist:
                            print(f"Book with ISBN {book.isbn} not found")
                except Exception as e:
                    print(f"Error importing student: {str(e)}")

            # Import pupils
            pupils_count = 0
            for pupil_obj in library_data['pupils']:
                try:
                    # Check if this pupil already exists
                    existing_pupil = Pupil.objects.filter(user_id=pupil_obj.user_id).first()
                    if existing_pupil:
                        # Update existing pupil
                        existing_pupil.name = pupil_obj.name
                        existing_pupil.surname = pupil_obj.surname
                        existing_pupil.group = pupil_obj.group
                        existing_pupil.age = pupil_obj.age
                        existing_pupil.save()
                    else:
                        # Create new pupil
                        pupil = Pupil(
                            user_id=pupil_obj.user_id,
                            name=pupil_obj.name,
                            surname=pupil_obj.surname,
                            group=pupil_obj.group,
                            age=pupil_obj.age
                        )
                        pupil.save()
                    pupils_count += 1

                    # Handle borrowed books
                    if existing_pupil:
                        pupil = existing_pupil
                    else:
                        pupil = Pupil.objects.get(user_id=pupil_obj.user_id)

                    # Clear existing borrowed books
                    pupil.borrowed_books.clear()

                    # Add borrowed books
                    for book in pupil_obj.borrowed_books.all():
                        try:
                            db_book = Book.objects.get(isbn=book.isbn)
                            pupil.borrowed_books.add(db_book)
                        except Book.DoesNotExist:
                            print(f"Book with ISBN {book.isbn} not found")
                except Exception as e:
                    print(f"Error importing pupil: {str(e)}")

            messages.success(request,
                             f"Successfully imported {books_count} books, {students_count} students, and {pupils_count} pupils")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Error deserializing library data: {str(e)}")
            return redirect('home')

    return render(request, 'library/deserialize_library.html')


def drop_all_data(request, silent=False):
    """Clear all library data"""
    # Get counts for display
    books_count = Book.objects.count()
    students_count = Student.objects.count()
    pupils_count = Pupil.objects.count()

    if request.method == 'POST' or silent:
        # Clear all data
        Book.objects.all().delete()
        Student.objects.all().delete()
        Pupil.objects.all().delete()

        if not silent:
            messages.success(request, "All library data has been cleared")
            return redirect('home')

    return render(request, 'library/drop_all_data.html', {
        'books_count': books_count,
        'students_count': students_count,
        'pupils_count': pupils_count
    })
# File Management Menu
def file_management(request):
    """Display file management options"""
    return render(request, 'library/file_management.html')

def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)

    return render(request, 'library/edit_book.html', {'form': form, 'book': book})


def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        # First check if anyone has borrowed this book
        if book.borrowed_by_students.exists() or book.borrowed_by_pupils.exists():
            messages.error(request, 'Cannot delete this book because it is currently borrowed by users.')
            return redirect('book_list')

        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('book_list')

    return render(request, 'library/delete_book.html', {'book': book})
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
    """Handle book borrowing requests."""
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            user_id = form.cleaned_data['user_id']
            book_id = form.cleaned_data['book_id']

            try:
                # Get the book and user objects
                book = get_object_or_404(Book, id=book_id)
                print(f"Book found: {book.title}, Quantity before: {book.quantity}")

                if user_type == 'student':
                    user = get_object_or_404(Student, user_id=user_id)
                else:  # pupil
                    user = get_object_or_404(Pupil, user_id=user_id)

                # Process the borrowing
                success, message = Library.process_borrowing(user, book)

                # Refresh the book data to get the updated quantity
                book.refresh_from_db()
                print(f"After borrowing: {book.title}, Quantity: {book.quantity}")

                if success:
                    messages.success(request, message)
                    # Redirect to book list to see the updated quantity
                    return redirect('book_list')
                else:
                    messages.error(request, message)
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                print(f"Exception during borrowing: {str(e)}")
    else:
        form = BorrowForm()

    return render(request, 'library/borrow_book.html', {'form': form})


def return_book(request):
    """Handle book return requests."""
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            user_id = form.cleaned_data['user_id']
            book_id = form.cleaned_data['book_id']

            try:
                # Get the book and user objects
                book = get_object_or_404(Book, id=book_id)
                print(f"Book found: {book.title}, Quantity before: {book.quantity}")

                if user_type == 'student':
                    user = get_object_or_404(Student, user_id=user_id)
                else:  # pupil
                    user = get_object_or_404(Pupil, user_id=user_id)

                # Process the return
                success, message = Library.process_return(user, book)

                # Refresh the book data to get the updated quantity
                book.refresh_from_db()
                print(f"After returning: {book.title}, Quantity: {book.quantity}")

                if success:
                    messages.success(request, message)
                    # Redirect to book list to see the updated quantity
                    return redirect('book_list')
                else:
                    messages.error(request, message)
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                print(f"Exception during return: {str(e)}")
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


def edit_student(request, user_id):
    student = get_object_or_404(Student, user_id=user_id)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('user_list')
    else:
        form = StudentForm(instance=student)

    return render(request, 'library/edit_student.html', {'form': form, 'student': student})


def edit_pupil(request, user_id):
    pupil = get_object_or_404(Pupil, user_id=user_id)

    if request.method == 'POST':
        form = PupilForm(request.POST, instance=pupil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pupil updated successfully.')
            return redirect('user_list')
    else:
        form = PupilForm(instance=pupil)

    return render(request, 'library/edit_pupil.html', {'form': form, 'pupil': pupil})


def delete_student(request, user_id):
    student = get_object_or_404(Student, user_id=user_id)

    if request.method == 'POST':
        # Check if the student has borrowed books
        if student.borrowed_books.exists():
            messages.error(request,
                           'Cannot delete this student because they currently have borrowed books. Please return all books first.')
            return redirect('user_list')

        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('user_list')

    return render(request, 'library/delete_student.html', {'student': student})


def delete_pupil(request, user_id):
    pupil = get_object_or_404(Pupil, user_id=user_id)

    if request.method == 'POST':
        # Check if the pupil has borrowed books
        if pupil.borrowed_books.exists():
            messages.error(request,
                           'Cannot delete this pupil because they currently have borrowed books. Please return all books first.')
            return redirect('user_list')

        pupil.delete()
        messages.success(request, 'Pupil deleted successfully.')
        return redirect('user_list')

    return render(request, 'library/delete_pupil.html', {'pupil': pupil})


def borrowed_books(request):
    """Display all books that are currently borrowed."""

    # Get all students who have borrowed books
    students_with_books = Student.objects.filter(borrowed_books__isnull=False).distinct()

    # Get all pupils who have borrowed books
    pupils_with_books = Pupil.objects.filter(borrowed_books__isnull=False).distinct()

    # Create a list to hold all borrowing records
    all_borrowings = []

    # Add student borrowings
    for student in students_with_books:
        for book in student.borrowed_books.all():
            all_borrowings.append({
                'user_type': 'student',
                'user_id': student.user_id,
                'user_name': f"{student.name} {student.surname}",
                'user_group': student.group,
                'book_id': book.id,
                'book_title': book.title,
                'book_author': book.author,
                'book_isbn': book.isbn,
                'book_label': book.get_label_display()
            })

    # Add pupil borrowings
    for pupil in pupils_with_books:
        for book in pupil.borrowed_books.all():
            all_borrowings.append({
                'user_type': 'pupil',
                'user_id': pupil.user_id,
                'user_name': f"{pupil.name} {pupil.surname}",
                'user_group': pupil.group,
                'user_age': pupil.age,
                'book_id': book.id,
                'book_title': book.title,
                'book_author': book.author,
                'book_isbn': book.isbn,
                'book_label': book.get_label_display()
            })

    # Sort the borrowings by user name and then book title
    all_borrowings.sort(key=lambda x: (x['user_name'], x['book_title']))

    # Count total borrowings
    total_borrowings = len(all_borrowings)

    # Count unique borrowers
    unique_borrowers = len(students_with_books) + len(pupils_with_books)

    return render(request, 'library/borrowed_books.html', {
        'borrowings': all_borrowings,
        'total_borrowings': total_borrowings,
        'unique_borrowers': unique_borrowers
    })


def edit_borrowing(request, user_type, user_id, book_id):
    # Get the book and user
    book = get_object_or_404(Book, id=book_id)

    if user_type == 'student':
        user = get_object_or_404(Student, user_id=user_id)
    else:  # pupil
        user = get_object_or_404(Pupil, user_id=user_id)

    # Verify that the user has borrowed this book
    if book not in user.borrowed_books.all():
        messages.error(request, f"This {user_type} has not borrowed this book.")
        return redirect('user_books', user_type=user_type, user_id=user_id)

    if request.method == 'POST':
        # Process the form: replace the borrowed book with another one
        new_book_id = request.POST.get('new_book_id')

        try:
            new_book = Book.objects.get(id=new_book_id)

            # Check if the new book can be borrowed by this user
            if not user.can_borrow(new_book):
                if user_type == 'pupil' and new_book.label != 'for children':
                    messages.error(request, "Pupils can only borrow books labeled as 'for children'.")
                elif hasattr(user, 'age') and user.age < 7:
                    messages.error(request, "Pupils under 7 years old cannot borrow books.")
                else:
                    messages.error(request, "This user cannot borrow the selected book.")
                return redirect('edit_borrowing', user_type=user_type, user_id=user_id, book_id=book_id)

            # Check if the new book is available
            if new_book.quantity <= 0:
                messages.error(request, "The selected book is not available.")
                return redirect('edit_borrowing', user_type=user_type, user_id=user_id, book_id=book_id)

            # Process the swap: return the old book and borrow the new one
            user.borrowed_books.remove(book)
            book.quantity += 1
            book.save()

            user.borrowed_books.add(new_book)
            new_book.quantity -= 1
            new_book.save()

            messages.success(request, f"Successfully swapped '{book.title}' for '{new_book.title}'.")
            return redirect('user_books', user_type=user_type, user_id=user_id)

        except Book.DoesNotExist:
            messages.error(request, "The selected book was not found.")
            return redirect('edit_borrowing', user_type=user_type, user_id=user_id, book_id=book_id)

    # If GET request, show the form with available books
    # Only show books that the user can borrow
    if user_type == 'student':
        available_books = Book.objects.filter(quantity__gt=0).exclude(id=book_id)
    else:  # pupil
        available_books = Book.objects.filter(quantity__gt=0, label='for children').exclude(id=book_id)

    return render(request, 'library/edit_borrowing.html', {
        'user': user,
        'user_type': user_type,
        'current_book': book,
        'available_books': available_books
    })