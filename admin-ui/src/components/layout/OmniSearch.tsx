import React, { useState, useRef, ChangeEvent, KeyboardEvent } from 'react';
import { Search, Paperclip, Zap } from 'lucide-react';

interface QuickAction {
  icon: string | React.ReactNode;
  label: string;
  domain: string;
  action?: () => void;
}

interface OmniSearchProps {
  onQuery: (text: string, files?: FileList) => void;
  quickActions?: QuickAction[];
  placeholder?: string;
}

const OmniSearch: React.FC<OmniSearchProps> = ({
  onQuery,
  quickActions = [],
  placeholder = "Ask anything or drop a file...",
}) => {
  const [queryText, setQueryText] = useState<string>('');
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setQueryText(event.target.value);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
      console.log('Files selected:', event.target.files);
    }
  };

  const handleSubmit = () => {
    if (queryText.trim() === '' && !selectedFiles) return;
    onQuery(queryText.trim(), selectedFiles || undefined);
    setQueryText('');
    setSelectedFiles(null);
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
    } else {
      console.log(`Quick Action clicked: ${quickAction.label} (Domain: ${quickAction.domain})`);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto p-2 bg-background dark:bg-gray-800 shadow-lg rounded-lg border border-border dark:border-gray-700">
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
          className="ml-2 px-4 py-2 bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] rounded-md text-sm font-medium hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[var(--theme-accent-primary)] focus:ring-opacity-50 transition-opacity"
        >
          Send
        </button>
      </div>
      
      {selectedFiles && selectedFiles.length > 0 && (
        <div className="mb-2 text-xs text-gray-500 dark:text-gray-400">
          Selected files: {Array.from(selectedFiles).map(f => f.name).join(', ')}
        </div>
      )}

      {quickActions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {quickActions.map((qa, index) => (
            <button
              key={index}
              onClick={() => handleQuickActionClick(qa)}
              title={qa.label}
              className="flex items-center px-2.5 py-1.5 bg-secondary dark:bg-gray-700 text-secondary-foreground dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full text-xs focus:outline-none focus:ring-1 focus:ring-[var(--theme-accent-primary)] transition-colors"
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
  );
};

export default OmniSearch; 