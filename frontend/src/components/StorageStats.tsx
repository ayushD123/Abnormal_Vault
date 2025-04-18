import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fileService } from '../services/fileService';
import { ChartBarIcon } from '@heroicons/react/24/outline';

interface StorageStatistics {
  total_files: number;
  unique_files: number;
  duplicate_files: number;
  total_size: number;
  actual_size: number;
  storage_saved: number;
  last_updated: string;
}

export const StorageStats: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['storage-statistics'],
    queryFn: fileService.getStorageStatistics,
    refetchInterval: 60000, // Refetch every minute
  });

  if (isLoading) {
    return (
      <div className="p-4 bg-white shadow rounded-lg">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return null;
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-4 bg-white shadow rounded-lg mb-4">
      <div className="flex items-center mb-3">
        <ChartBarIcon className="h-5 w-5 text-primary-600 mr-2" />
        <h3 className="text-lg font-medium leading-6 text-gray-900">Storage Statistics</h3>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-500">Total Files</p>
          <p className="text-xl font-semibold">{stats.total_files}</p>
        </div>
        
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-500">Unique Files</p>
          <p className="text-xl font-semibold">{stats.unique_files}</p>
        </div>
        
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-500">Total Storage</p>
          <p className="text-xl font-semibold">{formatBytes(stats.total_size)}</p>
        </div>
        
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-500">Storage Saved</p>
          <p className="text-xl font-semibold text-green-600">{formatBytes(stats.storage_saved)}</p>
        </div>
      </div>
      
      <div className="mt-3 text-xs text-gray-500 text-right">
        Last updated: {new Date(stats.last_updated).toLocaleString()}
      </div>
    </div>
  );
};