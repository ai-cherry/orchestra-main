/**
 * Natural Language Data Uploader Component for cherry-ai.me
 * 
 * This component provides an intuitive LLM-powered interface for data ingestion
 * with real-time duplicate detection and resolution feedback.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Loader2,
  MessageSquare,
  Zap,
  Database,
  GitBranch
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Type definitions
interface UploadProgress {
  fileId: string;
  filename: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'error' | 'duplicate';
  duplicateInfo?: {
    similarityScore: number;
    existingId: string;
    resolution: string;
  };
  message?: string;
}

interface DuplicateResolution {
  strategy: 'keep_existing' | 'replace' | 'merge' | 'keep_both' | 'manual';
  reason: string;
  confidence: number;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// Mock hooks for demonstration (would be implemented separately)
const useWebSocket = (url: string) => {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [readyState, setReadyState] = useState(WebSocket.CONNECTING);
  
  const sendMessage = (message: string) => {
    console.log('Sending WebSocket message:', message);
  };
  
  return { sendMessage, lastMessage, readyState };
};

const useLLMChat = (config: { systemPrompt: string }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  
  const sendMessage = async (message: string): Promise<any> => {
    setMessages(prev => [...prev, { role: 'user', content: message }]);
    setIsTyping(true);
    
    // Simulate LLM response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I understand your request and will process it accordingly.' 
      }]);
      setIsTyping(false);
    }, 1000);
    
    return { extractedContent: message, strategy: 'auto' };
  };
  
  return { sendMessage, messages, isTyping };
};

export const NaturalLanguageUploader: React.FC = () => {
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map());
  const [naturalQuery, setNaturalQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [duplicateResolutions, setDuplicateResolutions] = useState<Map<string, DuplicateResolution>>(new Map());
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // LLM chat hook for natural language processing
  const { sendMessage, messages, isTyping } = useLLMChat({
    systemPrompt: `You are a helpful data ingestion assistant for cherry-ai.me. 
    Help users upload and organize their data from various sources like Slack, Gong, Salesforce, Looker, and HubSpot.
    Detect data sources from context and provide clear feedback about duplicates and data organization.`
  });

  // WebSocket for real-time updates
  const { sendMessage: sendWsMessage, lastMessage, readyState } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL}/data-ingestion/ws/${Date.now()}`
  );

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      
      if (data.type === 'progress') {
        setUploads(prev => {
          const updated = new Map(prev);
          updated.set(data.fileId, {
            ...updated.get(data.fileId)!,
            progress: data.progress,
            status: data.status,
            message: data.message
          });
          return updated;
        });
      } else if (data.type === 'duplicate_detected') {
        handleDuplicateDetection(data);
      }
    }
  }, [lastMessage]);

  // Dropzone configuration
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsProcessing(true);

    // Create upload progress entries
    const newUploads = new Map(uploads);
    acceptedFiles.forEach(file => {
      const fileId = `${Date.now()}-${file.name}`;
      newUploads.set(fileId, {
        fileId,
        filename: file.name,
        progress: 0,
        status: 'pending'
      });
    });
    setUploads(newUploads);

    // Detect source type using LLM
    const fileContext = acceptedFiles.map(f => f.name).join(', ');
    const sourceDetection = await sendMessage(
      `What data source are these files from? Files: ${fileContext}`
    );

    // Upload files with deduplication
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('files', file);
      formData.append('source_type', detectSourceFromFilename(file.name));
      formData.append('deduplication_strategy', 'auto');
      formData.append('upload_channel', 'web_interface');

      try {
        const response = await fetch('/api/v1/data-ingestion/v2/upload/sync', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          }
        });

        const result = await response.json();
        
        // Update upload status
        result.forEach((fileResult: any) => {
          setUploads(prev => {
            const updated = new Map(prev);
            const fileId = `${Date.now()}-${file.name}`;
            updated.set(fileId, {
              ...updated.get(fileId)!,
              status: fileResult.duplicate_detected ? 'duplicate' : 'completed',
              duplicateInfo: fileResult.duplicate_info,
              message: fileResult.message
            });
            return updated;
          });
        });
      } catch (error) {
        console.error('Upload error:', error);
      }
    }

    setIsProcessing(false);
  }, [uploads, sendMessage]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'application/zip': ['.zip'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    }
  });

  // Handle natural language upload
  const handleNaturalLanguageUpload = async () => {
    if (!naturalQuery.trim()) return;

    setIsProcessing(true);

    // Send to LLM for interpretation
    const interpretation = await sendMessage(naturalQuery);

    // Extract content and metadata from natural language
    const uploadRequest = {
      query: naturalQuery,
      content: interpretation.extractedContent || naturalQuery,
      auto_detect_source: true
    };

    try {
      const response = await fetch('/api/v1/data-ingestion/v2/upload/natural-language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(uploadRequest)
      });

      const result = await response.json();
      
      // Add to chat as assistant response
      sendMessage(`I've processed your request: "${naturalQuery}". 
        ${result.duplicate_detected 
          ? `I found similar content with ${(result.duplicate_info.similarity_score * 100).toFixed(1)}% similarity. ${result.duplicate_info.recommendation}`
          : 'The content has been successfully uploaded with no duplicates found.'
        }`
      );

    } catch (error) {
      console.error('Natural language upload error:', error);
    }

    setIsProcessing(false);
    setNaturalQuery('');
  };

  // Handle duplicate detection
  const handleDuplicateDetection = async (data: any) => {
    // Ask LLM for resolution recommendation
    const recommendation = await sendMessage(
      `A duplicate was detected with ${(data.similarity_score * 100).toFixed(1)}% similarity. 
      The duplicate type is ${data.duplicate_type}. 
      What should we do? Keep existing, replace with new, merge, or keep both?`
    );

    setDuplicateResolutions(prev => {
      const updated = new Map(prev);
      updated.set(data.fileId, {
        strategy: recommendation.strategy || 'manual',
        reason: recommendation.reason || 'Manual review required',
        confidence: recommendation.confidence || 0.5
      });
      return updated;
    });
  };

  // Helper function to detect source from filename
  const detectSourceFromFilename = (filename: string): string => {
    const lower = filename.toLowerCase();
    if (lower.includes('slack')) return 'slack';
    if (lower.includes('gong')) return 'gong';
    if (lower.includes('salesforce') || lower.includes('sf_')) return 'salesforce';
    if (lower.includes('looker')) return 'looker';
    if (lower.includes('hubspot')) return 'hubspot';
    return 'auto';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">
          Intelligent Data Ingestion
        </h1>
        <p className="text-gray-600">
          Upload files or describe what you want to import using natural language
        </p>
      </div>

      {/* Natural Language Input */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-start space-x-3">
          <MessageSquare className="w-6 h-6 text-blue-500 mt-1" />
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe your data
            </label>
            <div className="flex space-x-3">
              <input
                type="text"
                value={naturalQuery}
                onChange={(e) => setNaturalQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleNaturalLanguageUpload()}
                placeholder="e.g., 'Upload our Q4 sales meeting notes from Slack' or 'Import the latest Gong call recordings'"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <button
                onClick={handleNaturalLanguageUpload}
                disabled={isProcessing || !naturalQuery.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                <span>Process</span>
              </button>
            </div>
          </div>
        </div>

        {/* Chat History */}
        {messages.length > 0 && (
          <div 
            ref={chatContainerRef}
            className="mt-4 max-h-60 overflow-y-auto space-y-3 p-4 bg-gray-50 rounded-lg"
          >
            {messages.map((msg: ChatMessage, idx: number) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 border border-gray-200 px-4 py-2 rounded-lg">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* File Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400 bg-white'
          }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          {isDragActive
            ? 'Drop files here...'
            : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Supports: Slack exports, Gong transcripts, Salesforce reports, Looker dashboards, HubSpot data
        </p>
      </div>

      {/* Upload Progress */}
      {uploads.size > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Database className="w-5 h-5" />
            <span>Processing Status</span>
          </h3>
          
          <AnimatePresence>
            {Array.from(uploads.values()).map((upload) => (
              <motion.div
                key={upload.fileId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-gray-500" />
                    <span className="font-medium text-gray-900">
                      {upload.filename}
                    </span>
                  </div>
                  <StatusIcon status={upload.status} />
                </div>

                {/* Progress Bar */}
                {upload.status === 'processing' && (
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress * 100}%` }}
                    />
                  </div>
                )}

                {/* Duplicate Info */}
                {upload.duplicateInfo && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <GitBranch className="w-5 h-5 text-yellow-600 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-yellow-800">
                          Duplicate Detected
                        </p>
                        <p className="text-sm text-yellow-700 mt-1">
                          {(upload.duplicateInfo.similarityScore * 100).toFixed(1)}% similar to existing content
                        </p>
                        {duplicateResolutions.has(upload.fileId) && (
                          <div className="mt-2 text-sm">
                            <span className="font-medium">Resolution: </span>
                            <span className="text-yellow-700">
                              {duplicateResolutions.get(upload.fileId)!.reason}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Status Message */}
                {upload.message && (
                  <p className="text-sm text-gray-600 mt-2">{upload.message}</p>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Real-time Connection Status */}
      <div className="fixed bottom-4 right-4">
        <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-2
          ${readyState === WebSocket.OPEN 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
          }`}
        >
          <div className={`w-2 h-2 rounded-full ${
            readyState === WebSocket.OPEN ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span>
            {readyState === WebSocket.OPEN ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

// Status Icon Component
const StatusIcon: React.FC<{ status: UploadProgress['status'] }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'error':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'duplicate':
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    case 'processing':
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    default:
      return <div className="w-5 h-5 rounded-full bg-gray-300" />;
  }
};

export default NaturalLanguageUploader;