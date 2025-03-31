# library/library.py (updated with fixed method name)
import re
from django.core.exceptions import ValidationError


class Library:
    @staticmethod
    def get_user_type(user_id):
        if not re.match(r'^\d{5}$', user_id):
            raise ValueError("User ID must be a 5-digit number.")

        if user_id.startswith('2'):
            return "Student"
        elif user_id.startswith('1'):
            return "Pupil"
        else:
            raise ValueError("Invalid user ID range. Student IDs start with '2', Pupil IDs start with '1'.")

    @staticmethod
    def process_borrowing(user, book):
        if not user.can_borrow(book):
            if hasattr(user, 'age') and user.age < 7:
                return False, "Pupils under 7 years old cannot borrow books."
            elif hasattr(user, 'age') and book.label != 'for children':
                return False, "Pupils can only borrow books labeled as 'for children'."
            return False, "This user cannot borrow this book."

        if book.quantity <= 0:
            return False, "This book is not available."

        if user.borrow_book(book):
            return True, "Book borrowed successfully."
        return False, "Failed to borrow the book."

    @staticmethod
    def process_return(user, book):
        if book not in user.borrowed_books.all():
            return False, "This user has not borrowed this book."

        if user.return_book(book):
            return True, "Book returned successfully."
        return False, "Failed to return the book."