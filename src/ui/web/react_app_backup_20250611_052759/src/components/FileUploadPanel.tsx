import React, { useState, useRef, useCallback } from 'react';
import { XMarkIcon, DocumentIcon, ArrowUpTrayIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface FileUploadPanelProps {
  onClose: () => void;
}

interface UploadFile {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

export const FileUploadPanel: React.FC<FileUploadPanelProps> = ({
  onClose,
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024; // 5GB
  const SUPPORTED_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/csv',
    'application/json',
    'application/zip',
    'image/jpeg',
    'image/png',
    'image/gif',
    'video/mp4',
    'video/avi',
    'video/mov',
    'audio/mp3',
    'audio/wav'
  ];

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('image')) return '🖼️';
    if (type.includes('video')) return '🎬';
    if (type.includes('audio')) return '🎵';
    if (type.includes('zip')) return '📦';
    if (type.includes('csv')) return '📊';
    if (type.includes('json')) return '⚙️';
    return '📎';
  };

  const validateFile = (file: File) => {
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds 5GB limit (${formatFileSize(file.size)})`;
    }
    if (!SUPPORTED_TYPES.includes(file.type)) {
      return `Unsupported file type: ${file.type}`;
    }
    return null;
  };

  const addFiles = useCallback((newFiles: File[]) => {
    const validFiles: UploadFile[] = [];
    
    newFiles.forEach(file => {
      const error = validateFile(file);
      if (error) {
        // Show error for invalid files
        setFiles(prev => [...prev, {
          file,
          id: `${file.name}-${Date.now()}`,
          progress: 0,
          status: 'error',
          error
        }]);
      } else {
        validFiles.push({
          file,
          id: `${file.name}-${Date.now()}`,
          progress: 0,
          status: 'pending'
        });
      }
    });

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, [addFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  }, [addFiles]);

  const simulateUpload = async (fileId: string) => {
    const fileIndex = files.findIndex(f => f.id === fileId);
    if (fileIndex === -1) return;

    // Update status to uploading
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, status: 'uploading' } : f
    ));

    // Simulate upload progress
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress } : f
      ));
    }

    // Switch to processing
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, status: 'processing', progress: 0 } : f
    ));

    // Simulate processing
    for (let progress = 0; progress <= 100; progress += 20) {
      await new Promise(resolve => setTimeout(resolve, 300));
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, progress } : f
      ));
    }

    // Complete
    setFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, status: 'completed', progress: 100 } : f
    ));
  };

  const handleUpload = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    for (const file of pendingFiles) {
      await simulateUpload(file.id);
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return 'text-blue-400';
      case 'uploading': return 'text-yellow-400';
      case 'processing': return 'text-purple-400';
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-white';
    }
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
      case 'error': return <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />;
      default: return null;
    }
  };

  return (
    <div className="w-full bg-white/5 rounded-xl border border-white/10 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-white mb-1">File Upload & Ingestion</h3>
          <p className="text-white/70 text-sm">
            Upload documents, images, videos, or any file up to 5GB for AI processing
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          <XMarkIcon className="w-5 h-5 text-white/70" />
        </button>
      </div>

      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200
          ${isDragOver 
            ? 'border-blue-400 bg-blue-400/10' 
            : 'border-white/30 hover:border-white/50'
          }
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <ArrowUpTrayIcon className="w-12 h-12 text-white/60 mx-auto mb-4" />
        <h4 className="text-lg font-medium text-white mb-2">
          Drag and drop files here
        </h4>
        <p className="text-white/60 mb-4">
          Or click to browse your files
        </p>
        
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
        >
          Choose Files
        </button>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept={SUPPORTED_TYPES.join(',')}
        />
        
        <div className="mt-4 text-xs text-white/50">
          <p>Supported: PDF, Word, Images, Videos, Audio, Text, CSV, JSON, ZIP</p>
          <p>Maximum file size: 5GB per file</p>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">
              Files ({files.length})
            </h4>
            {files.some(f => f.status === 'pending') && (
              <button
                onClick={handleUpload}
                className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors"
              >
                Upload All
              </button>
            )}
          </div>
          
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {files.map((uploadFile) => (
              <div
                key={uploadFile.id}
                className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/10"
              >
                {/* File Icon */}
                <div className="text-2xl">
                  {getFileIcon(uploadFile.file.type)}
                </div>
                
                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h5 className="font-medium text-white truncate">
                      {uploadFile.file.name}
                    </h5>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(uploadFile.status)}
                      <button
                        onClick={() => removeFile(uploadFile.id)}
                        className="p-1 hover:bg-white/10 rounded transition-colors"
                      >
                        <XMarkIcon className="w-4 h-4 text-white/60" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white/60">
                      {formatFileSize(uploadFile.file.size)}
                    </span>
                    <span className={getStatusColor(uploadFile.status)}>
                      {uploadFile.status === 'error' ? 'Error' : 
                       uploadFile.status === 'pending' ? 'Ready' :
                       uploadFile.status === 'uploading' ? 'Uploading...' :
                       uploadFile.status === 'processing' ? 'Processing...' :
                       'Completed'}
                    </span>
                  </div>
                  
                  {/* Progress Bar */}
                  {(uploadFile.status === 'uploading' || uploadFile.status === 'processing') && (
                    <div className="mt-2 w-full bg-white/20 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          uploadFile.status === 'uploading' ? 'bg-yellow-400' : 'bg-purple-400'
                        }`}
                        style={{ width: `${uploadFile.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {/* Error Message */}
                  {uploadFile.error && (
                    <div className="mt-1 text-xs text-red-400">
                      {uploadFile.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <h5 className="font-medium text-blue-400 mb-2">How it works:</h5>
        <ul className="text-sm text-blue-300 space-y-1">
          <li>• Files are automatically processed and indexed</li>
          <li>• Content becomes searchable across all AI personas</li>
          <li>• Large files are chunked for optimal processing</li>
          <li>• All data is securely stored and encrypted</li>
        </ul>
      </div>
    </div>
  );
}; 