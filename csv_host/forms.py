import os
from django import forms
from django.core.exceptions import ValidationError
from .models import CSVFile


class CSVFileUploadForm(forms.ModelForm):
    class Meta:
        model = CSVFile
        fields = ['title', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Sales Q3 Report (Leave blank to use filename)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv,text/csv'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes regarding what data is contained in this CSV'
            }),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext != '.csv':
                raise ValidationError('Only .csv files are supported.')
        return uploaded_file
