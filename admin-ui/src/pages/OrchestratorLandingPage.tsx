import React, { useEffect } from 'react';
import { Search, FileText, Mic } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { SearchInterface } from '../components/orchestrator/SearchInterface';
import { FileProgressTable } from '../components/orchestrator/FileManagement/FileProgressTable';
import { VoiceSynthesizer } from '../components/orchestrator/Voice/VoiceSynthesizer';
import useOrchestratorStore from '../store/orchestratorStore';
import { orchestratorService } from '../services/orchestratorService';
import websocketManager from '../services/websocketManager';

export const OrchestratorLandingPage: React.FC = () => {
  // Use Zustand store
  const {
    searchQuery,
    setSearchQuery,
    searchMode,
    setSearchMode,
    inputMode,
    setInputMode,
    suggestions,
    searchResults,
    isSearching,
    searchError,
    setIsSearching,
    setSearchResults,
    setSearchError,
    uploads,
    downloads,
    isWebSocketConnected,
  } = useOrchestratorStore();

  // Initialize WebSocket connection
  useEffect(() => {
    // Connect to WebSocket on mount
    websocketManager.connect();

    // Cleanup on unmount
    return () => {
      websocketManager.disconnect();
    };
  }, []);

  // Initialize with suggestions from API
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const suggestionsData = await orchestratorService.getSuggestions({
          userId: 'current-user', // TODO: Get from auth context
          sessionId: 'current-session',
        });
        const suggestionTexts = suggestionsData.map(s => s.text);
        useOrchestratorStore.getState().setSuggestions(suggestionTexts);
      } catch (error) {
        console.error('Failed to load suggestions:', error);
        // Fallback to default suggestions
        const defaultSuggestions = [
          'Analyze system performance metrics',
          'Generate workflow optimization report',
          'Create agent orchestration pipeline',
          'Debug integration issues',
        ];
        useOrchestratorStore.getState().setSuggestions(defaultSuggestions);
      }
    };
    
    loadSuggestions();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim() && inputMode === 'text') return;
    
    setIsSearching(true);
    setSearchError(null);
    
    try {
      // Send search query via WebSocket for real-time updates
      websocketManager.sendSearchQuery(searchQuery, searchMode);
      
      const results = await orchestratorService.search({
        query: searchQuery,
        mode: searchMode,
        inputMode: inputMode,
      });
      
      setSearchResults(results);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    // Optionally trigger search immediately
    handleSearch();
  };

  const hasFileActivity = uploads.length > 0 || downloads.length > 0;

  return (
    <div className="orchestrator-container">
      <div className="min-h-screen">
        {/* Header */}
        <div className="px-6 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">Orchestrator</h1>
                <p className="text-gray-400">Intelligent multi-modal search and orchestration</p>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isWebSocketConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-400">
                  {isWebSocketConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="px-6 pb-12">
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Search Interface */}
            <SearchInterface
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              searchMode={searchMode}
              setSearchMode={setSearchMode}
              inputMode={inputMode}
              setInputMode={setInputMode}
              onSearch={handleSearch}
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
            />

            {/* Results and Tools Area */}
            <Tabs defaultValue="results" className="w-full">
              <TabsList className="grid w-full grid-cols-3 bg-gray-800">
                <TabsTrigger value="results" className="data-[state=active]:bg-gray-700">
                  <Search className="w-4 h-4 mr-2" />
                  Results
                </TabsTrigger>
                <TabsTrigger value="files" className="data-[state=active]:bg-gray-700">
                  <FileText className="w-4 h-4 mr-2" />
                  Files {hasFileActivity && `(${uploads.length + downloads.length})`}
                </TabsTrigger>
                <TabsTrigger value="voice" className="data-[state=active]:bg-gray-700">
                  <Mic className="w-4 h-4 mr-2" />
                  Voice Synthesis
                </TabsTrigger>
              </TabsList>

              {/* Results Tab */}
              <TabsContent value="results">
                <Card className="orchestrator-card p-6">
                  {isSearching ? (
                    <div className="text-center py-12">
                      <div className="orchestrator-spinner mx-auto mb-4"></div>
                      <p className="text-gray-400">Searching...</p>
                    </div>
                  ) : searchError ? (
                    <div className="text-center py-12">
                      <p className="text-red-400 mb-2">Error: {searchError}</p>
                      <button
                        onClick={handleSearch}
                        className="text-[#e82626] hover:text-[#d01f1f] underline"
                      >
                        Try again
                      </button>
                    </div>
                  ) : searchResults.length > 0 ? (
                    <div className="space-y-4">
                      {searchResults.map((result) => (
                        <div
                          key={result.id}
                          className="orchestrator-result"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-white">{result.content}</p>
                              {result.metadata && (
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {Object.entries(result.metadata).map(([key, value]) => (
                                    <span
                                      key={key}
                                      className="text-xs px-2 py-1 bg-gray-800 rounded text-gray-400"
                                    >
                                      {key}: {String(value)}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <span className="text-xs text-gray-500 ml-4">
                              {result.type}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 mt-2">
                            {new Date(result.timestamp).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Search className="w-12 h-12 mx-auto mb-4" style={{ color: '#b89d9d' }} />
                      <p className="text-gray-400">Enter a query to see results</p>
                    </div>
                  )}
                </Card>
              </TabsContent>

              {/* Files Tab */}
              <TabsContent value="files">
                <FileProgressTable />
              </TabsContent>

              {/* Voice Synthesis Tab */}
              <TabsContent value="voice">
                <Card className="orchestrator-card p-6">
                  <h3 className="text-lg font-medium text-white mb-4">Text-to-Speech</h3>
                  <VoiceSynthesizer />
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};