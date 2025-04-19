# Update test_integration.py
import os
import io
import tempfile
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import File, StorageStatistics

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
        for root, dirs, files in os.walk(TEST_MEDIA_ROOT):
            for file in files:
                os.remove(os.path.join(root, file))
    
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
        
        # Compare as strings to handle UUID comparison issue
        self.assertEqual(str(duplicate_response.data['reference_file_id']), str(original_response.data['id']))
        
        # 3. Check statistics
        stats_response = self.client.get(self.statistics_url)
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertEqual(stats_response.data['total_files'], 2)
        self.assertEqual(stats_response.data['unique_files'], 1)
        self.assertEqual(stats_response.data['duplicate_files'], 1)
        self.assertEqual(stats_response.data['storage_saved'], len(content))

# Update tests.py - FileAPITests.test_duplicate_file_upload
def test_duplicate_file_upload(self):
    """Test uploading a duplicate file"""
    url = reverse('file-list')
    content = b"duplicate test content"
    
    # Upload original file
    original_file = io.BytesIO(content)
    original_file.name = 'original.txt'
    original_file.seek(0)
    
    original_response = self.client.post(url, {'file': original_file}, format='multipart')
    self.assertEqual(original_response.status_code, status.HTTP_201_CREATED)
    self.assertFalse(original_response.data['is_duplicate'])
    
    # Upload duplicate file
    duplicate_file = io.BytesIO(content)
    duplicate_file.name = 'duplicate.txt'
    duplicate_file.seek(0)
    
    duplicate_response = self.client.post(url, {'file': duplicate_file}, format='multipart')
    self.assertEqual(duplicate_response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(duplicate_response.data['is_duplicate'])
    
    # Compare as strings to handle UUID comparison issue
    self.assertEqual(str(duplicate_response.data['reference_file_id']), str(original_response.data['id']))
    
    # Verify both files exist but one is marked as duplicate
    self.assertEqual(File.objects.count(), 2)
    original = File.objects.get(id=original_response.data['id'])
    duplicate = File.objects.get(id=duplicate_response.data['id'])
    self.assertFalse(original.is_duplicate)
    self.assertTrue(duplicate.is_duplicate)
    self.assertEqual(duplicate.reference_file, original)