import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, AlertCircle } from 'lucide-react';
import { Card } from '../../ui/card';
import { Button } from '../../ui/button';
import useOrchestratorStore from '../../../store/orchestratorStore';
import { orchestratorService } from '../../../services/orchestratorService';


const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ACCEPTED_FILE_TYPES = {
  'text/*': ['.txt', '.md', '.csv', '.log'],
  'application/pdf': ['.pdf'],
  'application/json': ['.json'],
  'application/xml': ['.xml'],
  'application/zip': ['.zip'],
  'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
  'audio/*': ['.mp3', '.wav', '.ogg', '.m4a'],
  'video/*': ['.mp4', '.webm', '.mov'],
};

export const FileUploader: React.FC = () => {
  const [rejectedFiles, setRejectedFiles] = useState<any[]>([]);
  const { addUpload, updateUploadProgress, updateUploadStatus } = useOrchestratorStore();

  const onDrop = useCallback(async (acceptedFiles: File[], fileRejections: any[]) => {
    // Clear previous rejections
    setRejectedFiles(fileRejections);

    // Process accepted files
    for (const file of acceptedFiles) {
      // Add file to store
      addUpload(file);
      const uploadId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      try {
        // Update status to uploading
        updateUploadStatus(uploadId, 'uploading');

        // Upload file with progress tracking
        const result = await orchestratorService.uploadFile(file, (progress) => {
          updateUploadProgress(uploadId, progress);
        });

        if (result.status === 'success') {
          updateUploadStatus(uploadId, 'completed');
        } else {
          updateUploadStatus(uploadId, 'error', result.message);
        }
      } catch (error) {
        console.error('File upload error:', error);
        updateUploadStatus(uploadId, 'error', 'Failed to upload file');
      }
    }
  }, [addUpload, updateUploadProgress, updateUploadStatus]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    open,
  } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
    noClick: false,
    noKeyboard: false,
  });

  const getDropzoneStyles = () => {
    let baseStyles = 'border-2 border-dashed rounded-lg p-8 transition-all duration-200 cursor-pointer';
    
    if (isDragActive) {
      if (isDragAccept) {
        return `${baseStyles} border-green-500 bg-green-500/10`;
      }
      if (isDragReject) {
        return `${baseStyles} border-red-500 bg-red-500/10`;
      }
    }
    
    return `${baseStyles} border-gray-600 hover:border-gray-500 hover:bg-gray-800/50`;
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={getDropzoneStyles()}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <Upload className={`w-12 h-12 ${isDragActive ? 'text-blue-400' : 'text-gray-400'}`} />
            {isDragActive && (
              <div className="absolute inset-0 animate-ping">
                <Upload className="w-12 h-12 text-blue-400 opacity-75" />
              </div>
            )}
          </div>
          
          <div className="text-center">
            <p className="text-lg font-medium text-gray-300">
              {isDragActive
                ? isDragAccept
                  ? 'Drop files here'
                  : 'Invalid file type'
                : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to browse
            </p>
          </div>
          
          <div className="text-xs text-gray-600 text-center">
            <p>Supported formats: Text, PDF, JSON, XML, Images, Audio, Video</p>
            <p>Maximum file size: 50MB</p>
          </div>
        </div>
      </div>

      {/* Rejected files */}
      {rejectedFiles.length > 0 && (
        <Card className="p-4 bg-red-900/20 border-red-800">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-red-400 mb-2">
              <AlertCircle className="w-5 h-5" />
              <p className="font-medium">Some files were rejected:</p>
            </div>
            {rejectedFiles.map(({ file, errors }, index) => (
              <div key={index} className="text-sm text-red-300">
                <span className="font-medium">{file.name}</span>
                <ul className="ml-4 mt-1">
                  {errors.map((error: any, errorIndex: number) => (
                    <li key={errorIndex} className="text-red-400">
                      • {error.code === 'file-too-large' 
                          ? `File is larger than ${MAX_FILE_SIZE / 1024 / 1024}MB`
                          : error.message}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Alternative upload button */}
      <div className="flex justify-center">
        <Button
          onClick={open}
          variant="outline"
          className="gap-2"
        >
          <File className="w-4 h-4" />
          Select Files
        </Button>
      </div>
    </div>
  );
};