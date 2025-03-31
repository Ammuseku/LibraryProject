# library/models.py (updated with dynamic related_name)
from django.db import models
from django.core.exceptions import ValidationError
import re


class Book(models.Model):
    LABEL_CHOICES = [
        ('for children', 'For Children'),
        ('general', 'General'),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    year = models.IntegerField()
    quantity = models.IntegerField()
    label = models.CharField(max_length=20, choices=LABEL_CHOICES, default='general')

    def __str__(self):
        return self.title


class User(models.Model):
    user_id = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    group = models.CharField(max_length=50)

    # Note: this field is now defined in the child classes, not in the abstract User class

    class Meta:
        abstract = True

    def clean(self):
        # Validate user_id is 5 digits
        if not re.match(r'^\d{5}$', self.user_id):
            raise ValidationError("User ID must be a 5-digit number.")

    def borrow_book(self, book):
        if self.can_borrow(book) and book.quantity > 0:
            self.borrowed_books.add(book)
            book.quantity -= 1
            book.save()
            return True
        return False

    def return_book(self, book):
        """Return a borrowed book and update its quantity."""
        if book in self.borrowed_books.all():
            # First remove the book from the user's borrowed books
            self.borrowed_books.remove(book)

            # Then update the quantity
            book.quantity += 1
            book.save()

            # Debug print statement (optional, remove in production)
            print(f"Book '{book.title}' returned. New quantity: {book.quantity}")

            return True
        return False
    def check_user_type(self):
        if self.user_id.startswith('2'):
            return "This is a student"
        elif self.user_id.startswith('1'):
            return "This is a pupil"
        else:
            return "Unknown user type"

    def can_borrow(self, book):
        # To be overridden in subclasses
        return False

    def __str__(self):
        return f"{self.name} {self.surname} ({self.group})"


class Student(User):
    # Define borrowed_books here with a unique related_name
    borrowed_books = models.ManyToManyField(Book, blank=True, related_name='borrowed_by_students')

    def clean(self):
        super().clean()
        # Validate student ID starts with 2
        if not self.user_id.startswith('2'):
            raise ValidationError("Student ID must start with '2' (20000-29999).")

    def can_borrow(self, book):
        # Students can borrow any book
        return True


class Pupil(User):
    # Define borrowed_books here with a unique related_name
    borrowed_books = models.ManyToManyField(Book, blank=True, related_name='borrowed_by_pupils')
    age = models.IntegerField(default=7)

    def clean(self):
        super().clean()
        # Validate pupil ID starts with 1
        if not self.user_id.startswith('1'):
            raise ValidationError("Pupil ID must start with '1' (10000-19999).")

    def can_borrow(self, book):
        # Pupils can only borrow books labeled as "for children"
        # Optional: Age validation
        if self.age < 7:
            return False
        return book.label == 'for children'