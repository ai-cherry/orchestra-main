import React from 'react';
import { 
  Download, 
  Upload, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  FileText,
  ExternalLink
} from 'lucide-react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import useOrchestratorStore from '../../../store/orchestratorStore';

interface ProgressBarProps {
  progress: number;
  status: 'pending' | 'uploading' | 'downloading' | 'processing' | 'completed' | 'error';
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status }) => {
  const getProgressColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'processing':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        className={`h-full transition-all duration-300 ${getProgressColor()}`}
        style={{ width: `${Math.min(progress, 100)}%` }}
      />
    </div>
  );
};

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'error':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    case 'pending':
      return <Clock className="w-4 h-4 text-gray-500" />;
    case 'uploading':
      return <Upload className="w-4 h-4 text-blue-500" />;
    case 'downloading':
      return <Download className="w-4 h-4 text-blue-500" />;
    case 'processing':
      return <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />;
    default:
      return <FileText className="w-4 h-4 text-gray-500" />;
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatTime = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);
};

export const FileProgressTable: React.FC = () => {
  const { uploads, downloads, removeUpload, removeDownload } = useOrchestratorStore();

  const allFiles = [
    ...uploads.map(u => ({ ...u, direction: 'upload' as const })),
    ...downloads.map(d => ({ ...d, direction: 'download' as const })),
  ].sort((a, b) => {
    // Sort by timestamp, most recent first
    const timeA = 'uploadedAt' in a ? a.uploadedAt : a.downloadedAt;
    const timeB = 'uploadedAt' in b ? b.uploadedAt : b.downloadedAt;
    return timeB.getTime() - timeA.getTime();
  });

  if (allFiles.length === 0) {
    return (
      <Card className="p-8 text-center">
        <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500">No files in progress</p>
        <p className="text-sm text-gray-600 mt-1">
          Upload or download files to see them here
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left p-4 text-sm font-medium text-gray-400">File</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Size</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Progress</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Time</th>
              <th className="text-right p-4 text-sm font-medium text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody>
            {allFiles.map((file) => (
              <tr key={file.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                      {file.direction === 'upload' ? (
                        <Upload className="w-4 h-4 text-gray-500" />
                      ) : (
                        <Download className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-200 truncate">
                        {file.name}
                      </p>
                      {'type' in file && (
                        <p className="text-xs text-gray-500">{file.type || 'Unknown type'}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="text-sm text-gray-400">
                    {formatFileSize(file.size)}
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <StatusIcon status={file.status} />
                    <span className="text-sm text-gray-300 capitalize">
                      {file.status}
                    </span>
                  </div>
                </td>
                <td className="p-4 min-w-[200px]">
                  <div className="space-y-1">
                    <ProgressBar progress={file.progress} status={file.status} />
                    <p className="text-xs text-gray-500">{file.progress}%</p>
                  </div>
                </td>
                <td className="p-4">
                  <span className="text-sm text-gray-400">
                    {formatTime('uploadedAt' in file ? file.uploadedAt : file.downloadedAt)}
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex items-center justify-end gap-2">
                    {file.status === 'completed' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-gray-400 hover:text-white"
                        title="Open file"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    )}
                    {(file.status === 'uploading' || file.status === 'downloading') && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-400 hover:text-red-300"
                        onClick={() => {
                          if (file.direction === 'upload') {
                            removeUpload(file.id);
                          } else {
                            removeDownload(file.id);
                          }
                        }}
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                    {(file.status === 'completed' || file.status === 'error') && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-gray-400 hover:text-white"
                        onClick={() => {
                          if (file.direction === 'upload') {
                            removeUpload(file.id);
                          } else {
                            removeDownload(file.id);
                          }
                        }}
                        title="Remove from list"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};