import React, { useState } from 'react';
import { AdjustmentsHorizontalIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface FilterValues {
  search: string;
  fileType: string;
  sizeMin: string;
  sizeMax: string;
  uploadedFrom: string;
  uploadedTo: string;
}

interface SearchFilterProps {
  onFilterChange: (filters: Record<string, string>) => void;
}

export const SearchFilter: React.FC<SearchFilterProps> = ({ onFilterChange }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filterValues, setFilterValues] = useState<FilterValues>({
    search: '',
    fileType: '',
    sizeMin: '',
    sizeMax: '',
    uploadedFrom: '',
    uploadedTo: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilterValues(prev => ({ ...prev, [name]: value }));
  };

  const applyFilters = () => {
    // Convert filter values to an object with only non-empty values
    const filters = Object.entries(filterValues).reduce((acc, [key, value]) => {
      if (value) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    onFilterChange(filters);
  };

  const clearFilters = () => {
    setFilterValues({
      search: '',
      fileType: '',
      sizeMin: '',
      sizeMax: '',
      uploadedFrom: '',
      uploadedTo: '',
    });
    onFilterChange({});
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      {/* Basic search bar */}
      <div className="flex items-center">
        <div className="relative flex-grow">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            name="search"
            placeholder="Search files by name..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 sm:text-sm"
            value={filterValues.search}
            onChange={handleInputChange}
            onKeyPress={(e) => e.key === 'Enter' && applyFilters()}
          />
        </div>

        {/* Filter toggle button */}
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="ml-3 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <AdjustmentsHorizontalIcon className="h-4 w-4 mr-1" />
          Filters
        </button>

        {/* Apply filters button */}
        <button
          type="button"
          onClick={applyFilters}
          className="ml-3 inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Apply
        </button>

        {/* Clear filters button - only show if any filter is applied */}
        {Object.values(filterValues).some(v => v !== '') && (
          <button
            type="button"
            onClick={clearFilters}
            className="ml-3 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <XMarkIcon className="h-4 w-4 mr-1" />
            Clear
          </button>
        )}
      </div>

      {/* Advanced filters */}
      {isExpanded && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* File type filter */}
          <div>
            <label htmlFor="fileType" className="block text-sm font-medium text-gray-700">
              File Type
            </label>
            <select
              id="fileType"
              name="fileType"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
              value={filterValues.fileType}
              onChange={handleInputChange}
            >
              <option value="">All types</option>
              <option value="image/">Images</option>
              <option value="application/pdf">PDF</option>
              <option value="text/">Text</option>
              <option value="application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document">Documents</option>
              <option value="application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">Spreadsheets</option>
              <option value="application/zip,application/x-rar-compressed">Archives</option>
              <option value="video/">Videos</option>
              <option value="audio/">Audio</option>
            </select>
          </div>

          {/* Size range filter */}
          <div>
            <label htmlFor="sizeMin" className="block text-sm font-medium text-gray-700">
              Size range (KB)
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="number"
                name="sizeMin"
                placeholder="Min"
                className="focus:ring-primary-500 focus:border-primary-500 flex-1 block w-full rounded-l-md sm:text-sm border-gray-300"
                value={filterValues.sizeMin}
                onChange={handleInputChange}
                min="0"
              />
              <span className="inline-flex items-center px-3 rounded-none border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                to
              </span>
              <input
                type="number"
                name="sizeMax"
                placeholder="Max"
                className="focus:ring-primary-500 focus:border-primary-500 flex-1 block w-full rounded-r-md sm:text-sm border-gray-300"
                value={filterValues.sizeMax}
                onChange={handleInputChange}
                min="0"
              />
            </div>
          </div>

          {/* Date range filter */}
          <div>
            <label htmlFor="uploadedFrom" className="block text-sm font-medium text-gray-700">
              Upload date range
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="date"
                name="uploadedFrom"
                placeholder="From"
                className="focus:ring-primary-500 focus:border-primary-500 flex-1 block w-full rounded-l-md sm:text-sm border-gray-300"
                value={filterValues.uploadedFrom}
                onChange={handleInputChange}
              />
              <span className="inline-flex items-center px-3 rounded-none border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                to
              </span>
              <input
                type="date"
                name="uploadedTo"
                placeholder="To"
                className="focus:ring-primary-500 focus:border-primary-500 flex-1 block w-full rounded-r-md sm:text-sm border-gray-300"
                value={filterValues.uploadedTo}
                onChange={handleInputChange}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};