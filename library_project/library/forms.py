# library/forms.py
from django import forms
from .models import Book, Student, Pupil
import re


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'year', 'quantity', 'label']


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['user_id', 'name', 'surname', 'group']

    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']
        if not re.match(r'^\d{5}$', user_id):
            raise forms.ValidationError("User ID must be a 5-digit number.")
        if not user_id.startswith('2'):
            raise forms.ValidationError("Student ID must start with '2'.")
        return user_id


class PupilForm(forms.ModelForm):
    class Meta:
        model = Pupil
        fields = ['user_id', 'name', 'surname', 'group', 'age']

    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']
        if not re.match(r'^\d{5}$', user_id):
            raise forms.ValidationError("User ID must be a 5-digit number.")
        if not user_id.startswith('1'):
            raise forms.ValidationError("Pupil ID must start with '1'.")
        return user_id


class BorrowForm(forms.Form):
    USER_TYPES = [
        ('student', 'Student'),
        ('pupil', 'Pupil'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPES)
    user_id = forms.CharField(max_length=5)
    book_id = forms.IntegerField()


class ReturnForm(forms.Form):
    USER_TYPES = [
        ('student', 'Student'),
        ('pupil', 'Pupil'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPES)
    user_id = forms.CharField(max_length=5)
    book_id = forms.IntegerField()


class UserTypeCheckForm(forms.Form):
    user_id = forms.CharField(max_length=5)