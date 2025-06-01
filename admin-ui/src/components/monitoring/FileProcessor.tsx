import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, FileText, Image, Film, Music, Archive, CheckCircle, XCircle, Loader } from 'lucide-react';

interface ProcessedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  result?: any;
  error?: string;
}

const FileProcessor: React.FC = () => {
  const [files, setFiles] = useState<ProcessedFile[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'processing' as const,
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    // Simulate file processing
    newFiles.forEach((file, index) => {
      const interval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) => {
            if (f.id === file.id && f.status === 'processing') {
              const newProgress = f.progress + 10;
              if (newProgress >= 100) {
                clearInterval(interval);
                return {
                  ...f,
                  progress: 100,
                  status: Math.random() > 0.9 ? 'error' : 'completed',
                  result: { processed: true, metadata: { lines: 1234, entities: 56 } },
                  error: Math.random() > 0.9 ? 'Failed to process file' : undefined,
                };
              }
              return { ...f, progress: newProgress };
            }
            return f;
          })
        );
      }, 200 + index * 100);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/*': ['.txt', '.csv', '.json'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'application/pdf': ['.pdf'],
      'application/zip': ['.zip'],
    },
  });

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return Image;
    if (type.startsWith('video/')) return Film;
    if (type.startsWith('audio/')) return Music;
    if (type === 'application/zip') return Archive;
    if (type === 'application/pdf') return FileText;
    return File;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        File Processor
      </h3>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-300">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Supports: TXT, CSV, JSON, PDF, Images, ZIP
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Processing Queue ({files.length})
          </h4>
          {files.map((file) => {
            const Icon = getFileIcon(file.type);
            return (
              <div
                key={file.id}
                className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <Icon className="h-8 w-8 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {file.name}
                    </p>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                  
                  {file.status === 'processing' && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                        <span>Processing...</span>
                        <span>{file.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                        <div
                          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {file.status === 'completed' && file.result && (
                    <div className="mt-2 flex items-center space-x-4 text-xs">
                      <span className="text-green-600 dark:text-green-400 flex items-center">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Completed
                      </span>
                      <span className="text-gray-600 dark:text-gray-400">
                        Lines: {file.result.metadata?.lines || 'N/A'}
                      </span>
                      <span className="text-gray-600 dark:text-gray-400">
                        Entities: {file.result.metadata?.entities || 'N/A'}
                      </span>
                    </div>
                  )}

                  {file.status === 'error' && (
                    <div className="mt-2 flex items-center text-xs text-red-600 dark:text-red-400">
                      <XCircle className="h-3 w-3 mr-1" />
                      {file.error || 'Processing failed'}
                    </div>
                  )}
                </div>
                
                <div className="flex-shrink-0">
                  {file.status === 'processing' && (
                    <Loader className="h-5 w-5 text-blue-500 animate-spin" />
                  )}
                  {file.status === 'completed' && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {file.status === 'error' && (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FileProcessor; 