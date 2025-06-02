import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export type SearchMode = 'creative' | 'deep' | 'super_deep';
export type InputMode = 'text' | 'voice' | 'file';

export interface FileUpload {
  id: string;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  uploadedAt: Date;
}

export interface FileDownload {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  error?: string;
  downloadedAt: Date;
}

export interface SearchResult {
  id: string;
  content: string;
  type: 'text' | 'file' | 'voice';
  timestamp: Date;
  metadata?: Record<string, any>;
}

interface OrchestratorStore {
  // Search state
  searchQuery: string;
  searchMode: SearchMode;
  inputMode: InputMode;
  suggestions: string[];
  searchResults: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  
  // Voice state
  isRecording: boolean;
  selectedVoice: string;
  availableVoices: string[];
  transcription: string;
  audioBlob: Blob | null;
  
  // File state
  uploads: FileUpload[];
  downloads: FileDownload[];
  
  // WebSocket state
  isWebSocketConnected: boolean;
  
  // Actions - Search
  setSearchQuery: (query: string) => void;
  setSearchMode: (mode: SearchMode) => void;
  setInputMode: (mode: InputMode) => void;
  setSuggestions: (suggestions: string[]) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setIsSearching: (isSearching: boolean) => void;
  setSearchError: (error: string | null) => void;
  clearSearch: () => void;
  
  // Actions - Voice
  startRecording: () => void;
  stopRecording: () => void;
  setSelectedVoice: (voice: string) => void;
  setAvailableVoices: (voices: string[]) => void;
  setTranscription: (text: string) => void;
  setAudioBlob: (blob: Blob | null) => void;
  
  // Actions - File
  addUpload: (file: File) => void;
  updateUploadProgress: (id: string, progress: number) => void;
  updateUploadStatus: (id: string, status: FileUpload['status'], error?: string) => void;
  removeUpload: (id: string) => void;
  addDownload: (download: Omit<FileDownload, 'downloadedAt'>) => void;
  updateDownloadProgress: (id: string, progress: number) => void;
  updateDownloadStatus: (id: string, status: FileDownload['status'], error?: string) => void;
  removeDownload: (id: string) => void;
  
  // Actions - WebSocket
  setWebSocketConnected: (connected: boolean) => void;
  
  // Utility actions
  reset: () => void;
}

const initialState = {
  // Search state
  searchQuery: '',
  searchMode: 'creative' as SearchMode,
  inputMode: 'text' as InputMode,
  suggestions: [],
  searchResults: [],
  isSearching: false,
  searchError: null,
  
  // Voice state
  isRecording: false,
  selectedVoice: 'default',
  availableVoices: ['default'],
  transcription: '',
  audioBlob: null,
  
  // File state
  uploads: [],
  downloads: [],
  
  // WebSocket state
  isWebSocketConnected: false,
};

const useOrchestratorStore = create<OrchestratorStore>()(
  devtools(
    (set) => ({
      ...initialState,
      
      // Search actions
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchMode: (mode) => set({ searchMode: mode }),
      setInputMode: (mode) => set({ inputMode: mode }),
      setSuggestions: (suggestions) => set({ suggestions }),
      setSearchResults: (results) => set({ searchResults: results }),
      setIsSearching: (isSearching) => set({ isSearching }),
      setSearchError: (error) => set({ searchError: error }),
      clearSearch: () => set({ 
        searchResults: [], 
        searchError: null,
        isSearching: false 
      }),
      
      // Voice actions
      startRecording: () => set({ isRecording: true }),
      stopRecording: () => set({ isRecording: false }),
      setSelectedVoice: (voice) => set({ selectedVoice: voice }),
      setAvailableVoices: (voices) => set({ availableVoices: voices }),
      setTranscription: (text) => set({ transcription: text }),
      setAudioBlob: (blob) => set({ audioBlob: blob }),
      
      // File actions
      addUpload: (file) => set((state) => ({
        uploads: [...state.uploads, {
          id: `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          name: file.name,
          size: file.size,
          type: file.type,
          progress: 0,
          status: 'pending',
          uploadedAt: new Date(),
        }]
      })),
      
      updateUploadProgress: (id, progress) => set((state) => ({
        uploads: state.uploads.map(upload =>
          upload.id === id ? { ...upload, progress } : upload
        )
      })),
      
      updateUploadStatus: (id, status, error) => set((state) => ({
        uploads: state.uploads.map(upload =>
          upload.id === id ? { ...upload, status, error } : upload
        )
      })),
      
      removeUpload: (id) => set((state) => ({
        uploads: state.uploads.filter(upload => upload.id !== id)
      })),
      
      addDownload: (download) => set((state) => ({
        downloads: [...state.downloads, {
          ...download,
          downloadedAt: new Date(),
        }]
      })),
      
      updateDownloadProgress: (id, progress) => set((state) => ({
        downloads: state.downloads.map(download =>
          download.id === id ? { ...download, progress } : download
        )
      })),
      
      updateDownloadStatus: (id, status, error) => set((state) => ({
        downloads: state.downloads.map(download =>
          download.id === id ? { ...download, status, error } : download
        )
      })),
      
      removeDownload: (id) => set((state) => ({
        downloads: state.downloads.filter(download => download.id !== id)
      })),
      
      // WebSocket actions
      setWebSocketConnected: (connected) => set({ isWebSocketConnected: connected }),
      
      // Utility actions
      reset: () => set(initialState),
    }),
    {
      name: 'orchestrator-store',
    }
  )
);

export default useOrchestratorStore;