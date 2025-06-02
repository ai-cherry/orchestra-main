import React from 'react';
import { Input } from '../../ui/input';
import { Button } from '../../ui/button';
import { InputMode } from './index';
import { VoiceRecorder } from '../Voice/VoiceRecorder';
import { FileUploader } from '../FileManagement/FileUploader';

interface SearchInputProps {
  inputMode: InputMode;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSearch: () => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  inputMode,
  searchQuery,
  setSearchQuery,
  onSearch,
}) => {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearch();
    }
  };

  return (
    <>
      <div className="flex-1">
        {inputMode === 'text' && (
          <Input
            type="text"
            placeholder="Ask anything..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="orchestrator-input w-full"
          />
        )}
        {inputMode === 'voice' && (
          <div className="w-full">
            <VoiceRecorder />
          </div>
        )}
        {inputMode === 'file' && (
          <div className="w-full">
            <FileUploader />
          </div>
        )}
      </div>

      {/* Search Button - only show for text mode */}
      {inputMode === 'text' && (
        <Button
          className="orchestrator-btn-primary"
          onClick={onSearch}
          disabled={!searchQuery.trim()}
        >
          Search
        </Button>
      )}
    </>
  );
};