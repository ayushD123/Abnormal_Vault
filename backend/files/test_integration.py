# backend/files/test_integration.py
import os
import io
import tempfile
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import File, StorageStatistics

# Use temporary directory for media files during tests
TEST_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class FileIntegrationTests(APITestCase):
    """Integration tests for the file management system"""
    
    def setUp(self):
        """Set up test environment"""
        self.files_url = reverse('file-list')
        self.statistics_url = reverse('file-statistics')
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove all files in the test media directory
        for root, dirs, files in os.walk(TEST_MEDIA_ROOT):
            for file in files:
                os.remove(os.path.join(root, file))
    
    def test_complete_file_lifecycle(self):
        """Test complete lifecycle of a file: upload, retrieve, delete"""
        # 1. Upload a file
        file_content = b"Complete lifecycle test"
        file_obj = SimpleUploadedFile("lifecycle.txt", file_content, content_type="text/plain")
        
        upload_response = self.client.post(self.files_url, {'file': file_obj}, format='multipart')
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        file_id = upload_response.data['id']
        
        # 2. Retrieve the file details
        detail_url = reverse('file-detail', args=[file_id])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['original_filename'], 'lifecycle.txt')
        
        # 3. Delete the file
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 4. Verify file is deleted
        get_response = self.client.get(detail_url)
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_deduplication_workflow(self):
        """Test complete deduplication workflow with statistics update"""
        content = b"Deduplication test content"
        
        # 1. Upload original file
        original_file = SimpleUploadedFile("original_dedup.txt", content, content_type="text/plain")
        original_response = self.client.post(self.files_url, {'file': original_file}, format='multipart')
        self.assertEqual(original_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(original_response.data['is_duplicate'])
        
        # 2. Upload duplicate file
        duplicate_file = SimpleUploadedFile("duplicate_dedup.txt", content, content_type="text/plain")
        duplicate_response = self.client.post(self.files_url, {'file': duplicate_file}, format='multipart')
        self.assertEqual(duplicate_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(duplicate_response.data['is_duplicate'])
        self.assertEqual(duplicate_response.data['reference_file_id'], original_response.data['id'])
        
        # 3. Check statistics
        stats_response = self.client.get(self.statistics_url)
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertEqual(stats_response.data['total_files'], 2)
        self.assertEqual(stats_response.data['unique_files'], 1)
        self.assertEqual(stats_response.data['duplicate_files'], 1)
        self.assertEqual(stats_response.data['storage_saved'], len(content))
    
    def test_search_and_filter_workflow(self):
        """Test search and filter functionality together"""
        # Upload different files for testing
        file_types = [
            ("image.png", "image/png", b"PNG content", 1000),
            ("document.pdf", "application/pdf", b"PDF content", 5000),
            ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"Excel content", 3000),
            ("text.txt", "text/plain", b"Text content", 500),
        ]
        
        for filename, content_type, content, size in file_types:
            file_obj = SimpleUploadedFile(filename, content, content_type=content_type)
            self.client.post(self.files_url, {'file': file_obj}, format='multipart')
        
        # Test search functionality
        search_response = self.client.get(self.files_url, {'search': 'document'})
        self.assertEqual(len(search_response.data), 1)
        self.assertEqual(search_response.data[0]['original_filename'], 'document.pdf')
        
        # Test file type filter
        pdf_response = self.client.get(self.files_url, {'file_type': 'pdf'})
        self.assertEqual(len(pdf_response.data), 1)
        self.assertEqual(pdf_response.data[0]['file_type'], 'application/pdf')
        
        # Test size range filter
        large_files_response = self.client.get(self.files_url, {'size_min': 3000})
        self.assertEqual(len(large_files_response.data), 2)  # PDF and Excel files
        
        # Test combined search and filter
        combined_response = self.client.get(self.files_url, {'search': 'text', 'file_type': 'text'})
        self.assertEqual(len(combined_response.data), 1)
        self.assertEqual(combined_response.data[0]['original_filename'], 'text.txt')
    
    def test_bulk_operations(self):
        """Test operations with multiple files"""
        # Upload 10 files, with some duplicates
        content_a = b"Content A for bulk test"
        content_b = b"Content B for bulk test"
        
        for i in range(10):
            # Create alternating content to test deduplication
            content = content_a if i % 2 == 0 else content_b
            filename = f"bulk_file_{i}.txt"
            file_obj = SimpleUploadedFile(filename, content, content_type="text/plain")
            self.client.post(self.files_url, {'file': file_obj}, format='multipart')
        
        # Check statistics
        stats_response = self.client.get(self.statistics_url)
        self.assertEqual(stats_response.data['total_files'], 10)
        self.assertEqual(stats_response.data['unique_files'], 2)  # Only two unique contents
        self.assertEqual(stats_response.data['duplicate_files'], 8)
        
        # Verify ordering works with bulk data
        ordered_response = self.client.get(self.files_url, {'ordering': 'original_filename'})
        filenames = [file['original_filename'] for file in ordered_response.data]
        self.assertEqual(filenames, sorted(filenames))
    
    def test_error_handling(self):
        """Test API error handling scenarios"""
        # Test invalid file ID
        invalid_detail_url = reverse('file-detail', args=['invalid-uuid'])
        response = self.client.get(invalid_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test empty file upload
        response = self.client.post(self.files_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid ordering field
        response = self.client.get(self.files_url, {'ordering': 'invalid_field'})
        # Should still return results, just not ordered by the invalid field
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test invalid search term (should return empty results, not error)
        response = self.client.get(self.files_url, {'search': 'nonexistent_file'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)