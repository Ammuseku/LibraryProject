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

        from django.db import transaction

        try:
            with transaction.atomic():
                if user.borrow_book(book):
                    # Force a refresh from database to get updated quantity
                    book.refresh_from_db()
                    return True, f"Book '{book.title}' borrowed successfully. Remaining copies: {book.quantity}"
                return False, "Failed to borrow the book."
        except Exception as e:
            print(f"Error during borrowing process: {str(e)}")
            return False, f"An error occurred: {str(e)}"

    @staticmethod
    def process_return(user, book):
        """Process a book return request with proper validation."""
        # Print debug information
        print(f"Processing return request: User {user.user_id}, Book {book.id}, Current quantity: {book.quantity}")

        if book not in user.borrowed_books.all():
            return False, "This user has not borrowed this book."

        # Use Django transaction to ensure database consistency
        from django.db import transaction

        try:
            with transaction.atomic():
                if user.return_book(book):
                    # Force a refresh from database to get updated quantity
                    book.refresh_from_db()
                    return True, f"Book '{book.title}' returned successfully. New quantity: {book.quantity}"
                return False, "Failed to return the book."
        except Exception as e:
            print(f"Error during return process: {str(e)}")
            return False, f"An error occurred: {str(e)}"