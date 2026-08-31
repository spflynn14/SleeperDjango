import csv
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.views.generic import ListView, View
from django.db.models import Q
from .models import CSVFile
from .forms import CSVFileUploadForm


class CSVListView(ListView):
    model = CSVFile
    template_name = 'csv_host/list.html'
    context_object_name = 'csv_files'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(file__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload_form'] = CSVFileUploadForm()
        context['search_query'] = self.request.GET.get('q', '')
        # Build host prefix for formula helpers
        context['host_url'] = self.request.build_absolute_uri('/')[:-1]
        return context


class CSVUploadView(View):
    def post(self, request, *args, **kwargs):
        form = CSVFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_instance = form.save()
            messages.success(request, f'File "{csv_instance.title}" uploaded successfully!')
            return redirect('csv_host:preview', pk=csv_instance.pk)
        else:
            messages.error(request, 'Failed to upload CSV file. Please check the form errors.')
            # If upload fails from list page, render list with errors
            csv_files = CSVFile.objects.all()
            return render(request, 'csv_host/list.html', {
                'csv_files': csv_files,
                'upload_form': form,
                'host_url': request.build_absolute_uri('/')[:-1],
            })

    def get(self, request, *args, **kwargs):
        form = CSVFileUploadForm()
        return render(request, 'csv_host/upload.html', {'form': form})


def serve_raw_csv(request, pk, filename=None):
    """
    Serves raw CSV content with optimal headers for Google Sheets '=IMPORTDATA' function.
    """
    csv_file = get_object_or_404(CSVFile, pk=pk)
    if not csv_file.file or not os.path.exists(csv_file.file.path):
        raise Http404("CSV file not found on disk.")

    with open(csv_file.file.path, 'rb') as f:
        content = f.read()

    response = HttpResponse(content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'inline; filename="{csv_file.filename}"'
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def preview_csv(request, pk):
    """
    Renders an HTML table preview of the CSV content.
    """
    csv_file = get_object_or_404(CSVFile, pk=pk)
    if not csv_file.file or not os.path.exists(csv_file.file.path):
        raise Http404("CSV file not found on disk.")

    headers = []
    rows = []
    error_message = None

    try:
        with open(csv_file.file.path, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.reader(f)
            all_rows = list(reader)
            if all_rows:
                headers = all_rows[0]
                rows = all_rows[1:]
    except Exception as e:
        error_message = f"Error reading CSV content: {e}"

    raw_url = request.build_absolute_uri(csv_file.get_raw_url())
    google_sheets_formula = f'=IMPORTDATA("{raw_url}")'

    return render(request, 'csv_host/preview.html', {
        'csv_file': csv_file,
        'headers': headers,
        'rows': rows,
        'total_rows': len(rows),
        'total_columns': len(headers) if headers else 0,
        'raw_url': raw_url,
        'google_sheets_formula': google_sheets_formula,
        'error_message': error_message,
    })


def delete_csv(request, pk):
    if request.method == 'POST':
        csv_file = get_object_or_404(CSVFile, pk=pk)
        title = csv_file.title
        # Delete underlying file if it exists
        if csv_file.file and os.path.exists(csv_file.file.path):
            try:
                os.remove(csv_file.file.path)
            except OSError:
                pass
        csv_file.delete()
        messages.success(request, f'File "{title}" deleted successfully.')
    return redirect('csv_host:list')
