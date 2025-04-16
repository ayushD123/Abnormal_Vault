from django.db import models
import uuid
import os
import hashlib

def file_upload_path(instance, filename):
    """Generate file path for new file upload"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

def calculate_file_hash(file):
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)  # Reset file pointer to beginning
    return sha256_hash.hexdigest()

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64, db_index=True)  # SHA-256 hash
    is_duplicate = models.BooleanField(default=False)
    reference_file = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    @property
    def storage_saved(self):
        """Calculate storage saved if this is an original file with duplicates"""
        if not self.is_duplicate and hasattr(self, 'duplicates'):
            return self.size * self.duplicates.count()
        return 0

    def save(self, *args, **kwargs):
        """Override save method to calculate hash and check for duplicates"""
        if not self.file_hash:
            # Calculate the file hash
            self.file_hash = calculate_file_hash(self.file)
        
        # Check for duplicates
        existing_file = File.objects.filter(file_hash=self.file_hash, is_duplicate=False).first()
        if existing_file:
            # Mark as duplicate and reference the original file
            self.is_duplicate = True
            self.reference_file = existing_file
        else:
            # This is a unique file
            self.is_duplicate = False
            self.reference_file = None
        
        super().save(*args, **kwargs)
    

class StorageStatistics(models.Model):
    total_files = models.IntegerField(default=0)
    unique_files = models.IntegerField(default=0)
    duplicate_files = models.IntegerField(default=0)
    total_size = models.BigIntegerField(default=0)  # Total size of all files (including duplicates)
    actual_size = models.BigIntegerField(default=0)  # Actual storage used
    storage_saved = models.BigIntegerField(default=0)  # Storage saved by deduplication
    last_updated = models.DateTimeField(auto_now=True)
    
    @classmethod
    def update_statistics(cls):
        """Update storage statistics"""
        stats, created = cls.objects.get_or_create(id=1)
        
        # Get all files
        all_files = File.objects.all()
        unique_files = all_files.filter(is_duplicate=False)
        duplicate_files = all_files.filter(is_duplicate=True)
        
        stats.total_files = all_files.count()
        stats.unique_files = unique_files.count()
        stats.duplicate_files = duplicate_files.count()
        
        # Calculate sizes
        stats.total_size = sum(f.size for f in all_files)
        stats.actual_size = sum(f.size for f in unique_files)
        stats.storage_saved = stats.total_size - stats.actual_size
        
        stats.save()
        return stats
    
