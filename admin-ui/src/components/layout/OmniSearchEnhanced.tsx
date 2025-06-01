import React, { useState, useRef, ChangeEvent, KeyboardEvent } from 'react';
import { Search, Paperclip, Zap, Loader2, Sparkles, Brain, FileSearch, Globe } from 'lucide-react';
import { getPortkeyService } from '@/services/portkey/PortkeyService';

interface QuickAction {
  icon: string | React.ReactNode;
  label: string;
  domain: string;
  action?: () => void;
}

interface SearchResult {
  id: string;
  type: 'answer' | 'file' | 'action' | 'suggestion';
  content: string;
  source?: string;
  confidence?: number;
}

interface OmniSearchEnhancedProps {
  onQuery?: (text: string, files?: FileList) => void;
  onResult?: (result: SearchResult) => void;
  quickActions?: QuickAction[];
  placeholder?: string;
  enableAI?: boolean;
}

const OmniSearchEnhanced: React.FC<OmniSearchEnhancedProps> = ({
  onQuery,
  onResult,
  quickActions = [],
  placeholder = "Ask anything or drop a file...",
  enableAI = true,
}) => {
  const [queryText, setQueryText] = useState<string>('');
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [searchMode, setSearchMode] = useState<'smart' | 'web' | 'files'>('smart');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const defaultQuickActions: QuickAction[] = [
    {
      icon: <Brain />,
      label: 'Smart Search',
      domain: 'ai',
      action: () => setSearchMode('smart')
    },
    {
      icon: <Globe />,
      label: 'Web Search',
      domain: 'web',
      action: () => setSearchMode('web')
    },
    {
      icon: <FileSearch />,
      label: 'File Search',
      domain: 'files',
      action: () => setSearchMode('files')
    },
    ...quickActions
  ];

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setQueryText(event.target.value);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
    }
  };

  const performAISearch = async (query: string) => {
    if (!enableAI) {
      if (onQuery) onQuery(query, selectedFiles || undefined);
      return;
    }

    setIsSearching(true);
    setShowResults(true);
    
    try {
      const portkey = getPortkeyService();
      let result;
      
      switch (searchMode) {
        case 'web':
          // Use Perplexity for web search
          result = await portkey.searchAndGenerate(query);
          break;
        case 'files':
          // Use standard model with file context
          const fileContext = selectedFiles ? 
            `Analyzing files: ${Array.from(selectedFiles).map(f => f.name).join(', ')}\n\n` : '';
          result = await portkey.generateText(fileContext + query, {
            temperature: 0.3,
            maxTokens: 500
          });
          break;
        default:
          // Smart search - use best model
          result = await portkey.generateText(query, {
            model: 'gpt-4-turbo-preview',
            temperature: 0.7,
            maxTokens: 800
          });
      }
      
      if (result.success) {
        const searchResult: SearchResult = {
          id: Date.now().toString(),
          type: 'answer',
          content: typeof result.data === 'string' ? result.data : JSON.stringify(result.data) || 'No results found',
          source: searchMode,
          confidence: 0.95
        };
        
        setSearchResults([searchResult]);
        if (onResult) onResult(searchResult);
      }
    } catch (error: any) {
      console.error('Search error:', error);
      const errorResult: SearchResult = {
        id: Date.now().toString(),
        type: 'answer',
        content: `Search failed: ${error.message || 'Unknown error'}`,
        source: 'error',
        confidence: 0
      };
      setSearchResults([errorResult]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSubmit = () => {
    if (queryText.trim() === '' && !selectedFiles) return;
    
    performAISearch(queryText.trim());
    
    // Don't clear input for better UX
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleKeyPress = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickActionClick = (quickAction: QuickAction) => {
    if (quickAction.action) {
      quickAction.action();
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="p-2 bg-background dark:bg-gray-800 shadow-lg rounded-lg border border-border dark:border-gray-700">
        <div className="flex items-center border-b border-border dark:border-gray-700 pb-2 mb-2">
          <Search className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3 flex-shrink-0" />
          <input
            type="text"
            value={queryText}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="flex-grow p-2 bg-transparent text-foreground dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none text-sm"
          />
          <button
            onClick={triggerFileInput}
            title="Attach files"
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-accent-primary dark:hover:text-[var(--theme-accent-primary)] focus:outline-none transition-colors"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          <input
            type="file"
            ref={fileInputRef}
            multiple
            onChange={handleFileChange}
            className="hidden"
            accept=".zip,.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.txt,.md,.py,.js,.ts,.tsx,.html,.css,.json"
          />
          <button
            onClick={handleSubmit}
            disabled={isSearching}
            className="ml-2 px-4 py-2 bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] rounded-md text-sm font-medium hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[var(--theme-accent-primary)] focus:ring-opacity-50 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSearching ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Search</span>
              </>
            )}
          </button>
        </div>
        
        {selectedFiles && selectedFiles.length > 0 && (
          <div className="mb-2 text-xs text-gray-500 dark:text-gray-400">
            Selected files: {Array.from(selectedFiles).map(f => f.name).join(', ')}
          </div>
        )}

        {defaultQuickActions.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {defaultQuickActions.map((qa, index) => (
              <button
                key={index}
                onClick={() => handleQuickActionClick(qa)}
                title={qa.label}
                className={`flex items-center px-2.5 py-1.5 rounded-full text-xs focus:outline-none focus:ring-1 focus:ring-[var(--theme-accent-primary)] transition-colors ${
                  qa.domain === searchMode ? 
                  'bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)]' : 
                  'bg-secondary dark:bg-gray-700 text-secondary-foreground dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {typeof qa.icon === 'string' ? (
                  <span className="mr-1.5 text-sm">{qa.icon}</span>
                ) : (
                  React.cloneElement(qa.icon as React.ReactElement, { className: "mr-1.5 h-3.5 w-3.5" })
                )}
                {qa.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Search Results */}
      {showResults && searchResults.length > 0 && (
        <div className="mt-2 p-4 bg-background dark:bg-gray-800 shadow-lg rounded-lg border border-border dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">Results</h3>
            <button
              onClick={() => setShowResults(false)}
              className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Close
            </button>
          </div>
          <div className="space-y-2">
            {searchResults.map((result) => (
              <div key={result.id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{result.content}</p>
                    {result.source && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Source: {result.source} {result.confidence && `(${Math.round(result.confidence * 100)}% confidence)`}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OmniSearchEnhanced; 