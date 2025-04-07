# library/urls.py (complete updated version)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Book URLs
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('books/borrow/', views.borrow_book, name='borrow_book'),
    path('books/return/', views.return_book, name='return_book'),
    path('books/borrowed/', views.borrowed_books, name='borrowed_books'),

    # User URLs
    path('users/', views.user_list, name='user_list'),
    path('users/students/add/', views.add_student, name='add_student'),
    path('users/pupils/add/', views.add_pupil, name='add_pupil'),
    path('users/students/<str:user_id>/edit/', views.edit_student, name='edit_student'),
    path('users/pupils/<str:user_id>/edit/', views.edit_pupil, name='edit_pupil'),
    path('users/students/<str:user_id>/delete/', views.delete_student, name='delete_student'),
    path('users/pupils/<str:user_id>/delete/', views.delete_pupil, name='delete_pupil'),
    path('users/<str:user_type>/<str:user_id>/books/', views.user_books, name='user_books'),

    # Borrowing edit URL
    path('users/<str:user_type>/<str:user_id>/books/<int:book_id>/edit/',
         views.edit_borrowing,
         name='edit_borrowing'),

    # Utility URLs
    path('users/check/', views.check_user_type, name='check_user_type'),
    path('files/', views.file_management, name='file_management'),
    path('files/export-books-txt/', views.export_books_txt, name='export_books_txt'),
    path('files/import-books-txt/', views.import_books_txt, name='import_books_txt'),
    path('files/serialize-library/', views.serialize_library, name='serialize_library'),
    path('files/deserialize-library/', views.deserialize_library, name='deserialize_library'),
    path('files/drop-all-data/', views.drop_all_data, name='drop_all_data'),
]