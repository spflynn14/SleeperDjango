import os
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError


def validate_csv_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.csv':
        raise ValidationError('Only .csv files are supported.')


class CSVFile(models.Model):
    title = models.CharField(max_length=255, blank=True, help_text="Optional human-readable title for the CSV file")
    file = models.FileField(upload_to='csvs/', validators=[validate_csv_extension], help_text="Upload a .csv file")
    description = models.TextField(blank=True, help_text="Optional description of the dataset")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'CSV File'
        verbose_name_plural = 'CSV Files'

    def __str__(self):
        return self.title or self.filename

    def save(self, *args, **kwargs):
        if not self.title and self.file and self.file.name:
            self.title = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    @property
    def filename(self):
        if self.file and self.file.name:
            return os.path.basename(self.file.name)
        return ""

    @property
    def file_size(self):
        try:
            if self.file and os.path.exists(self.file.path):
                size = float(self.file.size)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
        except (OSError, ValueError):
            pass
        return "Unknown"

    def get_absolute_url(self):
        return reverse('csv_host:preview', kwargs={'pk': self.pk})

    def get_raw_url(self):
        return reverse('csv_host:raw_file', kwargs={'pk': self.pk, 'filename': self.filename})
