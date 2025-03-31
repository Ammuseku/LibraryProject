# library/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.add_book, name='add_book'),
    path('users/', views.user_list, name='user_list'),
    path('users/students/add/', views.add_student, name='add_student'),
    path('users/pupils/add/', views.add_pupil, name='add_pupil'),
    path('books/borrow/', views.borrow_book, name='borrow_book'),
    path('books/return/', views.return_book, name='return_book'),
    path('users/check/', views.check_user_type, name='check_user_type'),
    path('users/<str:user_type>/<str:user_id>/books/', views.user_books, name='user_books'),
]