# backend/files/tests.py
import os
import io
import hashlib
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import File, StorageStatistics, calculate_file_hash
from datetime import datetime, timedelta
from django.utils import timezone

class FileModelTests(TestCase):
    """Test cases for File model"""
    
    def create_test_file_content(self, content=b"test content"):
        """Helper method to create test file content"""
        file_content = io.BytesIO(content)
        file_content.seek(0)
        return file_content
    
    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        content = b"test content"
        file_content = self.create_test_file_content(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        calculated_hash = calculate_file_hash(file_content)
        
        self.assertEqual(calculated_hash, expected_hash)
        self.assertEqual(file_content.tell(), 0)  # Ensure file pointer is reset
    
    def test_file_creation(self):
        """Test basic file creation"""
        file_content = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")
        
        file_obj = File.objects.create(
            file=file_content,
            original_filename="test.txt",
            file_type="text/plain",
            size=len(b"test content")
        )
        
        self.assertIsNotNone(file_obj.id)
        self.assertEqual(file_obj.original_filename, "test.txt")
        self.assertEqual(file_obj.file_type, "text/plain")
        self.assertEqual(file_obj.size, len(b"test content"))
        self.assertIsNotNone(file_obj.file_hash)
        self.assertFalse(file_obj.is_duplicate)
        self.assertIsNone(file_obj.reference_file)
    
    def test_duplicate_file_detection(self):
        """Test that duplicate files are properly detected"""
        content = b"duplicate content"
        
        # Create original file
        original_file = SimpleUploadedFile("original.txt", content, content_type="text/plain")
        original = File.objects.create(
            file=original_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=len(content)
        )
        
        # Create duplicate file
        duplicate_file = SimpleUploadedFile("duplicate.txt", content, content_type="text/plain")
        duplicate = File.objects.create(
            file=duplicate_file,
            original_filename="duplicate.txt",
            file_type="text/plain",
            size=len(content)
        )
        
        self.assertFalse(original.is_duplicate)
        self.assertTrue(duplicate.is_duplicate)
        self.assertEqual(duplicate.reference_file, original)
        self.assertEqual(original.file_hash, duplicate.file_hash)
    
    def test_storage_saved_calculation(self):
        """Test storage saved calculation for original file with duplicates"""
        content = b"test content"
        size = len(content)
        
        # Create original file
        original_file = SimpleUploadedFile("original.txt", content, content_type="text/plain")
        original = File.objects.create(
            file=original_file,
            original_filename="original.txt",
            file_type="text/plain",
            size=size
        )
        
        # Create two duplicate files
        for i in range(2):
            duplicate_file = SimpleUploadedFile(f"duplicate{i}.txt", content, content_type="text/plain")
            File.objects.create(
                file=duplicate_file,
                original_filename=f"duplicate{i}.txt",
                file_type="text/plain",
                size=size
            )
        
        # Original file should show storage saved for its duplicates
        self.assertEqual(original.storage_saved, size * 2)
        
        # Check that duplicates have storage_saved = 0
        duplicate = File.objects.filter(is_duplicate=True).first()
        self.assertEqual(duplicate.storage_saved, 0)
    
    def test_file_upload_path(self):
        """Test that uploaded files get unique paths with UUID"""
        from .models import file_upload_path
        
        filename = "test.txt"
        instance = File()
        upload_path = file_upload_path(instance, filename)
        
        self.assertTrue(upload_path.startswith('uploads/'))
        self.assertTrue(upload_path.endswith('.txt'))
        # Check that filename is a UUID
        uuid_part = upload_path.split('/')[-1].split('.')[0]
        self.assertEqual(len(uuid_part), 36)  # UUID length

class StorageStatisticsTests(TestCase):
    """Test cases for StorageStatistics model"""
    
    def setUp(self):
        """Create test files for statistics testing"""
        self.content1 = b"unique content 1"
        self.content2 = b"unique content 2"
        self.duplicate_content = b"duplicate content"
        
        # Create unique files
        self.unique_file1 = File.objects.create(
            file=SimpleUploadedFile("file1.txt", self.content1),
            original_filename="file1.txt",
            file_type="text/plain",
            size=len(self.content1)
        )
        
        self.unique_file2 = File.objects.create(
            file=SimpleUploadedFile("file2.txt", self.content2),
            original_filename="file2.txt",
            file_type="text/plain",
            size=len(self.content2)
        )
        
        # Create original and duplicate files
        self.original_file = File.objects.create(
            file=SimpleUploadedFile("original.txt", self.duplicate_content),
            original_filename="original.txt",
            file_type="text/plain",
            size=len(self.duplicate_content)
        )
        
        self.duplicate_file1 = File.objects.create(
            file=SimpleUploadedFile("duplicate1.txt", self.duplicate_content),
            original_filename="duplicate1.txt",
            file_type="text/plain",
            size=len(self.duplicate_content)
        )
        
        self.duplicate_file2 = File.objects.create(
            file=SimpleUploadedFile("duplicate2.txt", self.duplicate_content),
            original_filename="duplicate2.txt",
            file_type="text/plain",
            size=len(self.duplicate_content)
        )
    
    def test_statistics_update(self):
        """Test that storage statistics are calculated correctly"""
        stats = StorageStatistics.update_statistics()
        
        self.assertEqual(stats.total_files, 5)
        self.assertEqual(stats.unique_files, 3)
        self.assertEqual(stats.duplicate_files, 2)
        
        # Total size includes all files (unique + duplicates)
        expected_total_size = (
            len(self.content1) + 
            len(self.content2) + 
            len(self.duplicate_content) * 3
        )
        self.assertEqual(stats.total_size, expected_total_size)
        
        # Actual size only includes unique files
        expected_actual_size = (
            len(self.content1) + 
            len(self.content2) + 
            len(self.duplicate_content)
        )
        self.assertEqual(stats.actual_size, expected_actual_size)
        
        # Storage saved is the size of duplicate files
        expected_storage_saved = len(self.duplicate_content) * 2
        self.assertEqual(stats.storage_saved, expected_storage_saved)

class FileAPITests(APITestCase):
    """Test cases for File API endpoints"""
    
    def test_file_list(self):
        """Test file listing API endpoint"""
        url = reverse('file-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No files yet
    
    def test_file_upload(self):
        """Test file upload API endpoint"""
        url = reverse('file-list')
        file_content = io.BytesIO(b"test upload content")
        file_content.name = 'test_upload.txt'
        file_content.seek(0)
        
        response = self.client.post(url, {'file': file_content}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_filename'], 'test_upload.txt')
        self.assertFalse(response.data['is_duplicate'])
        self.assertIsNotNone(response.data['file_hash'])
        
        # Verify file was created in database
        self.assertEqual(File.objects.count(), 1)
        file_obj = File.objects.first()
        self.assertEqual(file_obj.original_filename, 'test_upload.txt')
    
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
        self.assertEqual(duplicate_response.data['reference_file_id'], original_response.data['id'])
        
        # Verify both files exist but one is marked as duplicate
        self.assertEqual(File.objects.count(), 2)
        original = File.objects.get(id=original_response.data['id'])
        duplicate = File.objects.get(id=duplicate_response.data['id'])
        self.assertFalse(original.is_duplicate)
        self.assertTrue(duplicate.is_duplicate)
        self.assertEqual(duplicate.reference_file, original)
    
    def test_file_upload_validation(self):
        """Test file upload validation (no file provided)"""
        url = reverse('file-list')
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No file provided')
    
    def test_file_detail(self):
        """Test file detail API endpoint"""
        # Create a test file
        file_content = SimpleUploadedFile("test_detail.txt", b"detail content", content_type="text/plain")
        file_obj = File.objects.create(
            file=file_content,
            original_filename="test_detail.txt",
            file_type="text/plain",
            size=len(b"detail content")
        )
        
        url = reverse('file-detail', args=[file_obj.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_filename'], 'test_detail.txt')
    
    def test_file_delete(self):
        """Test file deletion API endpoint"""
        # Create a test file
        file_content = SimpleUploadedFile("test_delete.txt", b"delete content", content_type="text/plain")
        file_obj = File.objects.create(
            file=file_content,
            original_filename="test_delete.txt",
            file_type="text/plain",
            size=len(b"delete content")
        )
        
        url = reverse('file-detail', args=[file_obj.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(File.objects.count(), 0)
    
    def test_statistics_endpoint(self):
        """Test storage statistics API endpoint"""
        # Create some test files first
        content = b"test content"
        for i in range(3):
            file_content = SimpleUploadedFile(f"file{i}.txt", content, content_type="text/plain")
            File.objects.create(
                file=file_content,
                original_filename=f"file{i}.txt",
                file_type="text/plain",
                size=len(content)
            )
        
        url = reverse('file-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_files', response.data)
        self.assertIn('unique_files', response.data)
        self.assertIn('duplicate_files', response.data)
        self.assertIn('total_size', response.data)
        self.assertIn('actual_size', response.data)
        self.assertIn('storage_saved', response.data)
    
    def test_file_search(self):
        """Test file search functionality"""
        # Create multiple files with different names
        files_data = [
            ("document.pdf", "application/pdf"),
            ("image.png", "image/png"),
            ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ]
        
        for filename, file_type in files_data:
            file_content = SimpleUploadedFile(filename, b"content", content_type=file_type)
            File.objects.create(
                file=file_content,
                original_filename=filename,
                file_type=file_type,
                size=len(b"content")
            )
        
        # Test search by filename
        url = reverse('file-list')
        response = self.client.get(url, {'search': 'document'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'document.pdf')
    
    def test_file_filtering(self):
        """Test file filtering functionality"""
        # Create files with different types and sizes
        small_file = SimpleUploadedFile("small.txt", b"small", content_type="text/plain")
        large_file = SimpleUploadedFile("large.pdf", b"large" * 1000, content_type="application/pdf")
        
        past_date = timezone.now() - timedelta(days=2)
        
        # Create small file
        small = File.objects.create(
            file=small_file,
            original_filename="small.txt",
            file_type="text/plain",
            size=5
        )
        
        # Create large file
        large = File.objects.create(
            file=large_file,
            original_filename="large.pdf",
            file_type="application/pdf",
            size=5000
        )
        
        # Artificially set an older upload date for the small file
        File.objects.filter(id=small.id).update(uploaded_at=past_date)
        
        url = reverse('file-list')
        
        # Test file type filtering
        response = self.client.get(url, {'file_type': 'pdf'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'large.pdf')
        
        # Test size range filtering
        response = self.client.get(url, {'size_min': 1000})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'large.pdf')
        
        # Test date range filtering
        response = self.client.get(url, {'uploaded_from': past_date.date()})
        self.assertEqual(len(response.data), 2)
        
        # Test multiple file types
        response = self.client.get(url, {'file_type': 'text,pdf'})
        self.assertEqual(len(response.data), 2)
    
    def test_file_ordering(self):
        """Test file ordering functionality"""
        # Create files with different attributes
        files_data = [
            ("c_file.txt", 100),
            ("a_file.txt", 200),
            ("b_file.txt", 150),
        ]
        
        for filename, size in files_data:
            file_content = SimpleUploadedFile(filename, b"content", content_type="text/plain")
            File.objects.create(
                file=file_content,
                original_filename=filename,
                file_type="text/plain",
                size=size
            )
        
        url = reverse('file-list')
        
        # Test ordering by filename
        response = self.client.get(url, {'ordering': 'original_filename'})
        self.assertEqual(response.data[0]['original_filename'], 'a_file.txt')
        self.assertEqual(response.data[1]['original_filename'], 'b_file.txt')
        self.assertEqual(response.data[2]['original_filename'], 'c_file.txt')
        
        # Test reverse ordering by size
        response = self.client.get(url, {'ordering': '-size'})
        self.assertEqual(response.data[0]['original_filename'], 'a_file.txt')
        self.assertEqual(response.data[1]['original_filename'], 'b_file.txt')
        self.assertEqual(response.data[2]['original_filename'], 'c_file.txt')