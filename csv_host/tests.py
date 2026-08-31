import tempfile
import os
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CSVFile


class CSVHostTests(TestCase):
    def setUp(self):
        # Create a temporary directory for media files during tests
        self.temp_media_dir = tempfile.mkdtemp()
        self._media_override = override_settings(MEDIA_ROOT=self.temp_media_dir)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        # Clean up temp dir
        for root, dirs, files in os.walk(self.temp_media_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except OSError:
                    pass
            for dir_name in dirs:
                try:
                    os.rmdir(os.path.join(root, dir_name))
                except OSError:
                    pass
        try:
            os.rmdir(self.temp_media_dir)
        except OSError:
            pass

    def test_upload_valid_csv(self):
        csv_content = b"Name,Age,Score\nAlice,30,95\nBob,25,88\n"
        uploaded = SimpleUploadedFile("sample.csv", csv_content, content_type="text/csv")

        response = self.client.post(reverse('csv_host:upload'), {
            'title': 'Test Sample',
            'description': 'A sample test dataset',
            'file': uploaded,
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(CSVFile.objects.count(), 1)
        csv_obj = CSVFile.objects.first()
        self.assertEqual(csv_obj.title, 'Test Sample')
        self.assertEqual(csv_obj.description, 'A sample test dataset')
        self.assertTrue(csv_obj.filename.startswith('sample'))
        self.assertTrue(csv_obj.filename.endswith('.csv'))

    def test_upload_invalid_extension(self):
        invalid_content = b"Hello world text file"
        uploaded = SimpleUploadedFile("document.txt", invalid_content, content_type="text/plain")

        response = self.client.post(reverse('csv_host:upload'), {
            'title': 'Bad File',
            'file': uploaded,
        })

        self.assertEqual(CSVFile.objects.count(), 0)
        self.assertContains(response, 'Only .csv files are supported.')

    def test_serve_raw_csv_headers_and_content(self):
        csv_content = b"Item,Price,Quantity\nWidget,9.99,10\nGadget,19.99,5\n"
        uploaded = SimpleUploadedFile("inventory.csv", csv_content, content_type="text/csv")
        csv_obj = CSVFile.objects.create(title="Inventory", file=uploaded)

        # Request via /raw/<pk>/
        raw_url = reverse('csv_host:raw', kwargs={'pk': csv_obj.pk})
        response = self.client.get(raw_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('inline', response['Content-Disposition'])
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        self.assertEqual(response.content, csv_content)

        # Request via /raw/<pk>/<filename>
        raw_file_url = reverse('csv_host:raw_file', kwargs={'pk': csv_obj.pk, 'filename': csv_obj.filename})
        response_file = self.client.get(raw_file_url)
        self.assertEqual(response_file.status_code, 200)
        self.assertEqual(response_file.content, csv_content)

    def test_preview_csv(self):
        csv_content = b"Product,Category,InStock\nLaptop,Electronics,True\nChair,Furniture,False\n"
        uploaded = SimpleUploadedFile("products.csv", csv_content, content_type="text/csv")
        csv_obj = CSVFile.objects.create(title="Products List", file=uploaded)

        preview_url = reverse('csv_host:preview', kwargs={'pk': csv_obj.pk})
        response = self.client.get(preview_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Products List")
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Electronics")
        self.assertContains(response, "Chair")
        self.assertContains(response, "=IMPORTDATA(")
        self.assertEqual(response.context['total_rows'], 2)
        self.assertEqual(response.context['total_columns'], 3)
        self.assertEqual(response.context['headers'], ["Product", "Category", "InStock"])

    def test_search_csv_list(self):
        file1 = SimpleUploadedFile("q1_sales.csv", b"a,b\n1,2\n", content_type="text/csv")
        file2 = SimpleUploadedFile("q2_finance.csv", b"x,y\n3,4\n", content_type="text/csv")
        CSVFile.objects.create(title="Q1 Sales", file=file1)
        CSVFile.objects.create(title="Q2 Finance", file=file2)

        # Search for "Sales"
        response = self.client.get(reverse('csv_host:list'), {'q': 'Sales'})
        self.assertEqual(len(response.context['csv_files']), 1)
        self.assertEqual(response.context['csv_files'][0].title, "Q1 Sales")

    def test_delete_csv(self):
        csv_content = b"a,b\n1,2\n"
        uploaded = SimpleUploadedFile("to_delete.csv", csv_content, content_type="text/csv")
        csv_obj = CSVFile.objects.create(title="Delete Me", file=uploaded)
        file_path = csv_obj.file.path
        self.assertTrue(os.path.exists(file_path))

        delete_url = reverse('csv_host:delete', kwargs={'pk': csv_obj.pk})
        response = self.client.post(delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(CSVFile.objects.count(), 0)
        self.assertFalse(os.path.exists(file_path))

    def test_nonexistent_raw_returns_404(self):
        raw_url = reverse('csv_host:raw', kwargs={'pk': 99999})
        response = self.client.get(raw_url)
        self.assertEqual(response.status_code, 404)
