# conductor Landing Page - Component Specifications

## Component Interface Definitions

### Core Components

```typescript
// types/conductor.types.ts
export type InputMode = 'text' | 'voice' | 'file';
export type SearchMode = 'creative' | 'deep' | 'super_deep';
export type PanelType = 'search' | 'voice' | 'file' | 'suggestions';
export type FileStatus = 'queued' | 'downloading' | 'completed' | 'failed' | 'cancelled';

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  relevance: number;
  source: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Suggestion {
  id: string;
  text: string;
  category: 'recent' | 'trending' | 'recommended';
  icon?: string;
}

export interface FileUpload {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  error?: string;
}

export interface FileDownload {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: FileStatus;
  url?: string;
  error?: string;
  startedAt: string;
  completedAt?: string;
}

export interface VoiceOption {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  preview?: string;
}

export interface AppError {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  details?: any;
  timestamp: string;
}
```

### Layout Components

```typescript
// components/conductor/conductorLandingPage.tsx
import { FC, Suspense, lazy } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { useconductorStore } from '@/store/conductorStore';

const VoiceSection = lazy(() => import('./sections/VoiceSection'));
const FileManager = lazy(() => import('./sections/FileManager'));

export interface conductorLandingPageProps {
  className?: string;
  initialMode?: SearchMode;
  onSearchComplete?: (results: SearchResult[]) => void;
}

export const conductorLandingPage: FC<conductorLandingPageProps> = ({
  className,
  initialMode = 'creative',
  onSearchComplete,
}) => {
  const { ui, actions } = useconductorStore();
  
  return (
    <PageWrapper className={cn('conductor-landing', className)}>
      <Header />
      <main className="flex-1 overflow-hidden">
        <div className="container mx-auto px-4 py-6">
          <SearchSection initialMode={initialMode} />
          <MessageComposer />
          <SuggestionsPanel />
          
          <Suspense fallback={<LoadingSection />}>
            {ui.activePanel === 'voice' && <VoiceSection />}
            {ui.activePanel === 'file' && <FileManager />}
          </Suspense>
        </div>
      </main>
      <Footer />
    </PageWrapper>
  );
};

// components/conductor/layout/Header.tsx
export interface HeaderProps {
  user?: User;
  notifications?: Notification[];
  onNavigate?: (route: string) => void;
  className?: string;
}

export const Header: FC<HeaderProps> = ({
  user,
  notifications = [],
  onNavigate,
  className,
}) => {
  return (
    <header className={cn(
      'bg-[#181111] border-b border-[#382929]',
      'sticky top-0 z-50',
      className
    )}>
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Logo />
          <Navigation onNavigate={onNavigate} />
          <div className="flex items-center gap-4">
            <GlobalSearch />
            <NotificationBell notifications={notifications} />
            <UserProfile user={user} />
          </div>
        </div>
      </div>
    </header>
  );
};
```

### Search Components

```typescript
// components/conductor/search/SearchSection.tsx
export interface SearchSectionProps {
  initialMode?: SearchMode;
  className?: string;
}

export const SearchSection: FC<SearchSectionProps> = ({
  initialMode = 'creative',
  className,
}) => {
  const { search, actions } = useconductorStore();
  
  return (
    <section className={cn('search-section', className)}>
      <div className="flex items-center gap-4 mb-4">
        <InputModeSelector
          mode={search.inputMode}
          onChange={actions.setInputMode}
        />
        <SearchModeSelector
          mode={search.mode}
          onChange={actions.setSearchMode}
        />
      </div>
      
      <SearchInput
        value={search.query}
        onChange={actions.setQuery}
        onSubmit={actions.performSearch}
        isLoading={search.isSearching}
        error={search.error}
      />
      
      {search.results.length > 0 && (
        <SearchResults results={search.results} />
      )}
    </section>
  );
};

// components/conductor/search/SearchInput.tsx
export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  maxLength?: number;
  isLoading?: boolean;
  error?: string | null;
  className?: string;
}

export const SearchInput: FC<SearchInputProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = 'Ask anything...',
  maxLength = 1000,
  isLoading = false,
  error,
  className,
}) => {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };
  
  return (
    <div className={cn(
      'search-input-wrapper relative',
      'bg-[#261C1C] border border-[#382929] rounded-lg',
      'transition-all duration-200',
      isFocused && 'border-[#e82626] shadow-lg shadow-[#e82626]/20',
      error && 'border-red-500',
      className
    )}>
      <div className="flex items-start p-4">
        <SearchIcon className="w-6 h-6 text-gray-400 mt-1 mr-3" />
        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          maxLength={maxLength}
          disabled={isLoading}
          className={cn(
            'flex-1 bg-transparent text-white',
            'placeholder-gray-500 resize-none',
            'focus:outline-none',
            'min-h-[60px] max-h-[200px]'
          )}
          aria-label="Search query"
          aria-describedby={error ? 'search-error' : undefined}
        />
        {isLoading && (
          <LoadingSpinner className="ml-3" />
        )}
      </div>
      
      {error && (
        <div id="search-error" className="px-4 pb-2 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      <div className="px-4 pb-2 text-right text-gray-500 text-xs">
        {value.length}/{maxLength}
      </div>
    </div>
  );
};

// components/conductor/search/InputModeSelector.tsx
export interface InputModeSelectorProps {
  mode: InputMode;
  onChange: (mode: InputMode) => void;
  disabled?: boolean;
  className?: string;
}

export const InputModeSelector: FC<InputModeSelectorProps> = ({
  mode,
  onChange,
  disabled = false,
  className,
}) => {
  const modes: Array<{ value: InputMode; label: string; icon: string }> = [
    { value: 'text', label: 'Text', icon: 'edit' },
    { value: 'voice', label: 'Voice', icon: 'mic' },
    { value: 'file', label: 'File', icon: 'attach_file' },
  ];
  
  return (
    <div
      className={cn('input-mode-selector flex gap-2', className)}
      role="radiogroup"
      aria-label="Input mode"
    >
      {modes.map(({ value, label, icon }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          disabled={disabled}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg',
            'transition-all duration-200',
            'border border-[#382929]',
            mode === value
              ? 'bg-[#e82626] text-white border-[#e82626]'
              : 'bg-[#261C1C] text-gray-400 hover:text-white hover:border-gray-600'
          )}
          role="radio"
          aria-checked={mode === value}
          aria-label={`${label} input mode`}
        >
          <span className="material-icons-outlined text-sm">{icon}</span>
          <span className="text-sm font-medium">{label}</span>
        </button>
      ))}
    </div>
  );
};

// components/conductor/search/SearchModeSelector.tsx
export interface SearchModeSelectorProps {
  mode: SearchMode;
  onChange: (mode: SearchMode) => void;
  availableModes?: SearchMode[];
  className?: string;
}

export const SearchModeSelector: FC<SearchModeSelectorProps> = ({
  mode,
  onChange,
  availableModes = ['creative', 'deep', 'super_deep'],
  className,
}) => {
  const modeConfig: Record<SearchMode, { label: string; description: string }> = {
    creative: {
      label: 'Creative',
      description: 'Fast, creative responses',
    },
    deep: {
      label: 'Deep',
      description: 'Thorough analysis',
    },
    super_deep: {
      label: 'Super Deep',
      description: 'Comprehensive research',
    },
  };
  
  return (
    <div className={cn('search-mode-selector', className)}>
      <Select
        value={mode}
        onValueChange={(value) => onChange(value as SearchMode)}
      >
        <SelectTrigger className="w-[180px] bg-[#261C1C] border-[#382929]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="bg-[#261C1C] border-[#382929]">
          {availableModes.map((modeOption) => (
            <SelectItem
              key={modeOption}
              value={modeOption}
              className="text-white hover:bg-[#382929]"
            >
              <div>
                <div className="font-medium">{modeConfig[modeOption].label}</div>
                <div className="text-xs text-gray-400">
                  {modeConfig[modeOption].description}
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
```

### Voice Components

```typescript
// components/conductor/voice/VoiceRecorder.tsx
export interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  onError: (error: Error) => void;
  language?: string;
  maxDuration?: number;
  className?: string;
}

export const VoiceRecorder: FC<VoiceRecorderProps> = ({
  onTranscription,
  onError,
  language = 'en-US',
  maxDuration = 60000, // 60 seconds
  className,
}) => {
  const { voice, actions } = useconductorStore();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100); // Collect data every 100ms
      actions.startRecording();
      
      // Auto-stop after max duration
      timerRef.current = setTimeout(() => {
        stopRecording();
      }, maxDuration);
      
    } catch (error) {
      onError(new Error('Failed to access microphone'));
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      actions.stopRecording();
      
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }
  };
  
  const processAudio = async (audioBlob: Blob) => {
    try {
      const response = await voiceAPI.transcribe({
        audio: audioBlob,
        format: 'webm',
        language,
      });
      
      onTranscription(response.transcription);
      actions.setTranscription(response.transcription);
    } catch (error) {
      onError(new Error('Transcription failed'));
    }
  };
  
  return (
    <div className={cn('voice-recorder', className)}>
      <div className="flex flex-col items-center gap-4">
        <button
          onClick={voice.isRecording ? stopRecording : startRecording}
          className={cn(
            'w-20 h-20 rounded-full flex items-center justify-center',
            'transition-all duration-300',
            voice.isRecording
              ? 'bg-red-600 animate-pulse'
              : 'bg-[#e82626] hover:bg-red-700'
          )}
          aria-label={voice.isRecording ? 'Stop recording' : 'Start recording'}
        >
          <span className="material-icons-outlined text-white text-3xl">
            {voice.isRecording ? 'stop' : 'mic'}
          </span>
        </button>
        
        {voice.isRecording && (
          <div className="text-center">
            <div className="text-white mb-2">Recording...</div>
            <div className="text-gray-400 text-sm">
              {formatDuration(voice.recordingDuration)}
            </div>
            <VoiceVisualizer />
          </div>
        )}
        
        {voice.transcription && !voice.isRecording && (
          <div className="bg-[#261C1C] border border-[#382929] rounded-lg p-4 max-w-md">
            <div className="text-gray-400 text-sm mb-2">Transcription:</div>
            <div className="text-white">{voice.transcription}</div>
          </div>
        )}
      </div>
    </div>
  );
};

// components/conductor/voice/VoiceSynthesizer.tsx
export interface VoiceSynthesizerProps {
  text: string;
  voice: VoiceOption;
  onComplete?: () => void;
  onError?: (error: Error) => void;
  className?: string;
}

export const VoiceSynthesizer: FC<VoiceSynthesizerProps> = ({
  text,
  voice,
  onComplete,
  onError,
  className,
}) => {
  const { voice: voiceState, actions } = useconductorStore();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const synthesizeSpeech = async () => {
    try {
      actions.synthesizeSpeech(text);
      
      const response = await voiceAPI.synthesize({
        text,
        voiceId: voice.id,
        options: {
          speed: 1.0,
          pitch: 0,
          volume: 1.0,
          format: 'mp3',
        },
      });
      
      if (audioRef.current) {
        audioRef.current.src = response.audioUrl;
        audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (error) {
      onError?.(new Error('Speech synthesis failed'));
    }
  };
  
  const togglePlayback = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };
  
  return (
    <div className={cn('voice-synthesizer', className)}>
      <div className="bg-[#261C1C] border border-[#382929] rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">Text-to-Speech</h3>
          <VoiceSelector
            selectedVoice={voice}
            onChange={actions.setSelectedVoice}
          />
        </div>
        
        <div className="mb-4">
          <textarea
            value={text}
            readOnly
            className="w-full bg-[#181111] text-white p-3 rounded border border-[#382929]"
            rows={3}
          />
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={synthesizeSpeech}
            disabled={!text || voiceState.isSynthesizing}
            className={cn(
              'px-4 py-2 rounded-lg flex items-center gap-2',
              'bg-[#e82626] text-white',
              'hover:bg-red-700 disabled:opacity-50'
            )}
          >
            <span className="material-icons-outlined text-sm">record_voice_over</span>
            <span>Generate Speech</span>
          </button>
          
          {voiceState.audioUrl && (
            <button
              onClick={togglePlayback}
              className="p-2 rounded-lg bg-[#382929] text-white hover:bg-gray-700"
            >
              <span className="material-icons-outlined">
                {isPlaying ? 'pause' : 'play_arrow'}
              </span>
            </button>
          )}
        </div>
        
        <audio
          ref={audioRef}
          onEnded={() => {
            setIsPlaying(false);
            onComplete?.();
          }}
          onError={() => onError?.(new Error('Audio playback failed'))}
        />
      </div>
    </div>
  );
};
```

### File Management Components

```typescript
// components/conductor/files/FileUploader.tsx
export interface FileUploaderProps {
  onUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  maxFiles?: number;
  onError?: (error: FileError) => void;
  className?: string;
}

export const FileUploader: FC<FileUploaderProps> = ({
  onUpload,
  acceptedTypes = ['*/*'],
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  onError,
  className,
}) => {
  const { files, actions } = useconductorStore();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer?.files || []);
    handleFiles(droppedFiles);
  };
  
  const handleFiles = (selectedFiles: File[]) => {
    const validFiles: File[] = [];
    const errors: FileError[] = [];
    
    selectedFiles.forEach((file) => {
      // Check file count
      if (validFiles.length >= maxFiles) {
        errors.push({
          file: file.name,
          error: `Maximum ${maxFiles} files allowed`,
        });
        return;
      }
      
      // Check file size
      if (file.size > maxSize) {
        errors.push({
          file: file.name,
          error: `File size exceeds ${formatFileSize(maxSize)}`,
        });
        return;
      }
      
      // Check file type
      if (acceptedTypes[0] !== '*/*') {
        const isAccepted = acceptedTypes.some(type => {
          if (type.endsWith('/*')) {
            return file.type.startsWith(type.slice(0, -2));
          }
          return file.type === type;
        });
        
        if (!isAccepted) {
          errors.push({
            file: file.name,
            error: 'File type not accepted',
          });
          return;
        }
      }
      
      validFiles.push(file);
    });
    
    if (errors.length > 0) {
      errors.forEach(error => onError?.(error));
    }
    
    if (validFiles.length > 0) {
      onUpload(validFiles);
      actions.uploadFiles(validFiles);
    }
  };
  
  return (
    <div className={cn('file-uploader', className)}>
      <div
        onDragEnter={handleDragEnter}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8',
          'transition-all duration-200 cursor-pointer',
          'text-center',
          isDragging
            ? 'border-[#e82626] bg-[#e82626]/10'
            : 'border-[#382929] hover:border-gray-600'
        )}
      >
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-[#261C1C] flex items-center justify-center">
            <span className="material-icons-outlined text-gray-400 text-2xl">
              cloud_upload
            </span>
          </div>
          
          <div>
            <p className="text-white font-medium mb-1">
              Drop files here or click to upload
            </p>
            <p className="text-gray-400 text-sm">
              Maximum {maxFiles} files, up to {formatFileSize(maxSize)} each
            </p>
          </div>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple={maxFiles > 1}
          accept={acceptedTypes.join(',')}
          onChange={(e) => handleFiles(Array.from(e.target.files || []))}
          className="hidden"
        />
      </div>
      
      {files.uploads.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.uploads.map((upload) => (
            <FileUploadItem key={upload.id} upload={upload} />
          ))}
        </div>
      )}
    </div>
  );
};

// components/conductor/files/DownloadTable.tsx
export interface DownloadTableProps {
  downloads: FileDownload[];
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  onOpen: (id: string) => void;
  className?: string;
}

export const DownloadTable: FC<DownloadTableProps> = ({
  downloads,
  onCancel,
  onRetry,
  onOpen,
  className,
}) => {
  const sortedDownloads = useMemo(
    () => [...downloads].sort((a, b) => 
      new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
    ),
    [downloads]
  );
  
  return (
    <div className={cn('download-table', className)}>
      <div className="bg-[#261C1C] border border-[#382929] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#382929]">
              <th className="px-4 py-3 text-left text-gray-400 font-medium">File</th>
              <th className="px-4 py-3 text-left text-gray-400 font-medium">Size</th>
              <th className="px-4 py-3 text-left text-gray-400 font-medium">Status</th>
              <th className="px-4 py-3 text-left text-gray-400 font-medium">Progress</th>
              <th className="px-4 py-3 text-right text-gray-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedDownloads.map((download) => (
              <DownloadTableRow
                key={download.id}
                download={download}
                onCancel={onCancel}
                onRetry={onRetry}
                onOpen={onOpen}
              />
            ))}
          </tbody>
        </table>
        
        {downloads.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No downloads yet
          </div>
        )}
      </div>
    </div>
  );
};

// components/conductor/files/DownloadTableRow.tsx
interface DownloadTableRowProps {
  download: FileDownload;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  onOpen: (id: string) => void;
}

const DownloadTableRow: FC<DownloadTableRowProps> = ({
  download,
  onCancel,
  onRetry,
  onOpen,
}) => {
  const statusConfig: Record<FileStatus, { icon: string; color: string }> = {
    queued: { icon: 'schedule', color: 'text-gray-400' },
    downloading: { icon: 'downloading', color: 'text-blue-400' },
    completed: { icon: 'check_circle', color: 'text-green-400' },
    failed: { icon: 'error', color: 'text-red-400' },
    cancelled: { icon: 'cancel', color: 'text-gray-500' },
  };
  
  const config = statusConfig[download.status];
  
  return (
    <tr className="border-b border-[#382929] hover:bg-[#1a1414]">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <FileIcon filename={download.name} />
          <div>
            <div className="text-white font-medium">{download.name}</div>
            <div className="text-gray-500 text-xs">
              Started {formatRelativeTime(download.startedAt)}
            </div>
          </div>
        </div>
      </td>
      
      <td className="px-4 py-3 text-gray-400">
        {formatFileSize(download.size)}
      </td>
      
      <td className="px-4 py-3">
        <div className={cn('flex items-center gap-2', config.color)}>
          <span className="material-icons-outlined text-sm">{config.icon}</span>
          <span className="capitalize">{download.status}</span>
        </div>
      </td>
      
      <td className="px-4 py-3">
        {download.status === 'downloading' ? (
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-[#181111] rounded-full h-2 overflow-hidden">
              <div
                className="bg-[#e82626] h-full transition-all duration-300"
                style={{ width: `${download.progress}%` }}
              />
            </div>
            <span className="text-gray-400 text-sm">{download.progress}%</span>
          </div>
        ) : (
          <span className="text-gray-500">—</span>
        )}
      </td>
      
      <td className="px-4 py-3">
        <div className="flex items-center justify-end gap-2">
          {download.status === 'downloading' && (
            <button
              onClick={() => onCancel(download.id)}
              className="p-1 rounded hover:bg-[#382929] text-gray-400 hover:text-white"
              aria-label="Cancel download"
            >
              <span className="material-icons-outlined text-sm">close</span>
            </button>
          )}
          
          {download.status === 'failed' && (
            <button
              onClick={() => onRetry(download.id)}
              className="p-1 rounded hover:bg-[#382929] text-gray-400 hover:text-white"
              aria-label="Retry download"
            >
              <span className="material-icons-outlined text-sm">refresh</span