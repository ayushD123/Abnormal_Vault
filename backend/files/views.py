from django.shortcuts import render
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateTimeFilter, RangeFilter, CharFilter, NumberFilter
from .models import File, StorageStatistics, calculate_file_hash
from .serializers import FileSerializer, StorageStatisticsSerializer

# Custom filter set for File model
class FileFilter(FilterSet):
    # Date range filtering
    uploaded_from = DateTimeFilter(field_name='uploaded_at', lookup_expr='gte')
    uploaded_to = DateTimeFilter(field_name='uploaded_at', lookup_expr='lte')
    
    # Size range filtering (e.g., size_min=1000&size_max=5000)
    size_min = NumberFilter(field_name='size', lookup_expr='gte')  # Fixed import issue
    size_max = NumberFilter(field_name='size', lookup_expr='lte')  # Fixed import issue
    
    # File type filtering (supports multiple values with comma separation)
    file_type = CharFilter(method='filter_file_type')
    
    def filter_file_type(self, queryset, name, value):
        if value:
            file_types = [ft.strip() for ft in value.split(',')]
            q = Q()
            for ft in file_types:
                q |= Q(file_type__icontains=ft)
            return queryset.filter(q)
        return queryset
    
    class Meta:
        model = File
        fields = ['file_type', 'size_min', 'size_max', 'uploaded_from', 'uploaded_to']

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['original_filename']  # Enable searching by filename
    filterset_class = FileFilter
    ordering_fields = ['uploaded_at', 'original_filename', 'size', 'file_type']
    ordering = ['-uploaded_at']  # Default ordering

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_obj)
        
        # Check if a file with the same hash already exists
        existing_file = File.objects.filter(file_hash=file_hash, is_duplicate=False).first()
        
        if existing_file:
            # Create a reference to the existing file
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash,
                'is_duplicate': True,
                'reference_file': existing_file.id  # Use the ID of the existing file
            }
        else:
            # This is a new unique file
            data = {
                'file': file_obj,
                'original_filename': file_obj.name,
                'file_type': file_obj.content_type,
                'size': file_obj.size,
                'file_hash': file_hash,
                'is_duplicate': False
            }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Update storage statistics
        StorageStatistics.update_statistics()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get storage statistics"""
        stats = StorageStatistics.update_statistics()
        serializer = StorageStatisticsSerializer(stats)
        return Response(serializer.data)