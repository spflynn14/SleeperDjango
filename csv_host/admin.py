from django.contrib import admin
from .models import CSVFile


@admin.register(CSVFile)
class CSVFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'filename', 'file_size', 'uploaded_at', 'updated_at')
    search_fields = ('title', 'description', 'file')
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at', 'updated_at', 'file_size', 'filename')
