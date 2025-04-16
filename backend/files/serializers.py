from rest_framework import serializers
from .models import File, StorageStatistics

class FileSerializer(serializers.ModelSerializer):
    storage_saved = serializers.ReadOnlyField()
    is_duplicate = serializers.ReadOnlyField()
    reference_file_id = serializers.PrimaryKeyRelatedField(read_only=True, source='reference_file')
    
    class Meta:
        model = File
        fields = ['id', 'file', 'original_filename', 'file_type', 'size', 
                 'uploaded_at', 'file_hash', 'is_duplicate', 'reference_file_id', 'storage_saved']
        read_only_fields = ['id', 'uploaded_at', 'file_hash', 'is_duplicate', 'reference_file_id', 'storage_saved']

class StorageStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageStatistics
        fields = ['total_files', 'unique_files', 'duplicate_files', 
                 'total_size', 'actual_size', 'storage_saved', 'last_updated']