from django.urls import path
from . import views

app_name = 'csv_host'

urlpatterns = [
    path('', views.CSVListView.as_view(), name='list'),
    path('upload/', views.CSVUploadView.as_view(), name='upload'),
    path('raw/<int:pk>/', views.serve_raw_csv, name='raw'),
    path('raw/<int:pk>/<str:filename>', views.serve_raw_csv, name='raw_file'),
    path('preview/<int:pk>/', views.preview_csv, name='preview'),
    path('delete/<int:pk>/', views.delete_csv, name='delete'),
]
