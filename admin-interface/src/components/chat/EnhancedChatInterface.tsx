import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Volume2, VolumeX, Settings, Search, Presentation, Image, Music, Video, FileText } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { Badge } from '../ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { usePersona } from '../../contexts/PersonaContext';
import PortkeyService from '../../services/portkeyService';
import SearchService from '../../services/searchService';
import SlideSpeakService from '../../services/slideSpeakService';
import ElevenLabsService from '../../services/elevenLabsService';
import AILearningService from '../../services/aiLearningService';
import AirbyteCloudService from '../../services/airbyteService';
import NotionWorkflowService from '../../services/notionWorkflowService';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  persona: 'sophia' | 'karen' | 'cherry';
  type: 'text' | 'audio' | 'search_results' | 'presentation' | 'media';
  metadata?: any;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
  persona?: 'sophia' | 'karen' | 'cherry';
}

const EnhancedChatInterface: React.FC = () => {
  const { currentPersona, switchPersona, getPersonaConfig } = usePersona();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [searchMode, setSearchMode] = useState<'normal' | 'deep' | 'super_deep'>('normal');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Services
  const portkeyService = new PortkeyService();
  const searchService = new SearchService();
  const slideSpeakService = new SlideSpeakService();
  const elevenLabsService = new ElevenLabsService();
  const aiLearningService = new AILearningService();
  const airbyteService = new AirbyteCloudService();
  const notionWorkflowService = new NotionWorkflowService();

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize voice recognition
    if ('webkitSpeechRecognition' in window) {
      const recognition = new (window as any).webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      (window as any).speechRecognition = recognition;
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
      persona: currentPersona,
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Get AI learning recommendations
      const recommendations = aiLearningService.getPersonalizedRecommendations(currentPersona);
      
      // Enhance query with AI learning
      const enhancedQuery = aiLearningService.enhanceSearchQuery(
        inputValue,
        currentPersona,
        { timestamp: new Date(), type: 'chat' }
      );

      // Determine if this is a search, creation, or general query
      const intent = await detectIntent(inputValue);
      
      let aiResponse: Message;

      switch (intent.type) {
        case 'search':
          aiResponse = await handleSearchIntent(inputValue, intent, enhancedQuery);
          break;
        case 'create_presentation':
          aiResponse = await handlePresentationIntent(inputValue, intent);
          break;
        case 'create_media':
          aiResponse = await handleMediaIntent(inputValue, intent);
          break;
        case 'workflow':
          aiResponse = await handleWorkflowIntent(inputValue, intent);
          break;
        default:
          aiResponse = await handleGeneralIntent(inputValue, enhancedQuery);
      }

      setMessages(prev => [...prev, aiResponse]);

      // Track interaction for learning
      aiLearningService.trackInteraction(
        currentPersona,
        intent.type,
        { query: inputValue, intent },
        'success',
        0.9
      );

      // Generate voice response if enabled
      if (voiceEnabled && aiResponse.content) {
        await generateVoiceResponse(aiResponse.content);
      }

    } catch (error) {
      console.error('Error processing message:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
        persona: currentPersona,
        type: 'text'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }

    const recognition = (window as any).speechRecognition;
    
    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
    }
  };

  const handlePersonaSwitch = (persona: 'sophia' | 'karen' | 'cherry') => {
    switchPersona(persona);
    
    // Add system message about persona switch
    const switchMessage: Message = {
      id: Date.now().toString(),
      content: `Switched to ${persona.charAt(0).toUpperCase() + persona.slice(1)} persona. I'm now optimized for ${getPersonaDescription(persona)}.`,
      sender: 'ai',
      timestamp: new Date(),
      persona: persona,
      type: 'text'
    };
    
    setMessages(prev => [...prev, switchMessage]);
  };

  const detectIntent = async (query: string): Promise<{ type: string; confidence: number; parameters: any }> => {
    // Use Portkey to analyze intent
    const response = await portkeyService.generateResponse(
      `Analyze this query and determine the intent. Return JSON with type, confidence, and parameters: "${query}"`,
      currentPersona,
      { temperature: 0.1 }
    );

    try {
      return JSON.parse(response);
    } catch {
      return { type: 'general', confidence: 0.5, parameters: {} };
    }
  };

  const handleSearchIntent = async (
    query: string,
    intent: any,
    enhancedQuery: any
  ): Promise<Message> => {
    // Combine internal and external search
    const [internalResults, externalResults] = await Promise.all([
      airbyteService.enhancedSearch(query, currentPersona, {
        search_mode: enhancedQuery.search_mode,
        result_limit: 10
      }),
      searchService.search(enhancedQuery.enhanced_query, currentPersona, enhancedQuery.search_mode)
    ]);

    const combinedResults = {
      internal: internalResults.internal_results,
      external: externalResults.results,
      sources: [...internalResults.data_sources, ...externalResults.sources],
      metadata: {
        search_time: internalResults.search_metadata.search_time_ms,
        total_results: internalResults.internal_results.length + externalResults.results.length
      }
    };

    // Generate AI summary of results
    const summary = await portkeyService.generateResponse(
      `Summarize these search results for ${currentPersona}: ${JSON.stringify(combinedResults)}`,
      currentPersona
    );

    return {
      id: Date.now().toString(),
      content: summary,
      sender: 'ai',
      timestamp: new Date(),
      persona: currentPersona,
      type: 'search_results',
      metadata: combinedResults
    };
  };

  const handlePresentationIntent = async (query: string, intent: any): Promise<Message> => {
    // Extract topic from query
    const topic = intent.parameters.topic || query.replace(/create presentation about|make a presentation on/i, '').trim();
    
    // Search for relevant information
    const searchResults = await searchService.search(topic, currentPersona, 'deep');
    
    // Create presentation using SlideSpeak
    const presentation = await slideSpeakService.createPresentation(
      topic,
      currentPersona,
      {
        content: searchResults.results.slice(0, 10),
        style: getPersonaConfig(currentPersona).presentationStyle
      }
    );

    return {
      id: Date.now().toString(),
      content: `I've created a presentation about "${topic}" with ${presentation.slide_count} slides. The presentation includes comprehensive research and is optimized for ${currentPersona}'s style.`,
      sender: 'ai',
      timestamp: new Date(),
      persona: currentPersona,
      type: 'presentation',
      metadata: presentation
    };
  };

  const handleMediaIntent = async (query: string, intent: any): Promise<Message> => {
    const mediaType = intent.parameters.media_type;
    
    switch (mediaType) {
      case 'song':
        // Generate song using ElevenLabs
        const songAudio = await elevenLabsService.generateSpeech(
          intent.parameters.lyrics || query,
          currentPersona,
          { emotion: 'creative' }
        );
        
        return {
          id: Date.now().toString(),
          content: `I've created a song for you! The audio has been generated with ${currentPersona}'s voice style.`,
          sender: 'ai',
          timestamp: new Date(),
          persona: currentPersona,
          type: 'media',
          metadata: { type: 'audio', data: songAudio }
        };
        
      case 'image':
        // This would integrate with image generation service
        return {
          id: Date.now().toString(),
          content: `I would create an image here. Integration with image generation service needed.`,
          sender: 'ai',
          timestamp: new Date(),
          persona: currentPersona,
          type: 'media',
          metadata: { type: 'image' }
        };
        
      default:
        return {
          id: Date.now().toString(),
          content: `I can help create ${mediaType}, but this feature is still being implemented.`,
          sender: 'ai',
          timestamp: new Date(),
          persona: currentPersona,
          type: 'text'
        };
    }
  };

  const handleWorkflowIntent = async (query: string, intent: any): Promise<Message> => {
    // Get workflow suggestions
    const suggestions = await notionWorkflowService.getWorkflowSuggestions(
      currentPersona,
      messages.slice(-10).map(m => m.content)
    );

    return {
      id: Date.now().toString(),
      content: `I found ${suggestions.suggested_workflows.length} workflow automation opportunities for you. Would you like me to set up any of these automated processes?`,
      sender: 'ai',
      timestamp: new Date(),
      persona: currentPersona,
      type: 'text',
      metadata: suggestions
    };
  };

  const handleGeneralIntent = async (query: string, enhancedQuery: any): Promise<Message> => {
    const response = await portkeyService.generateResponse(
      enhancedQuery.enhanced_query,
      currentPersona,
      {
        temperature: 0.7,
        context: messages.slice(-5).map(m => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.content }))
      }
    );

    return {
      id: Date.now().toString(),
      content: response,
      sender: 'ai',
      timestamp: new Date(),
      persona: currentPersona,
      type: 'text'
    };
  };

  const generateVoiceResponse = async (text: string) => {
    if (!voiceEnabled) return;

    try {
      setIsSpeaking(true);
      
      const audioBuffer = await elevenLabsService.generateSpeech(
        text,
        currentPersona,
        { emotion: 'friendly' }
      );

      // Convert ArrayBuffer to audio URL and play
      const audioBlob = new Blob([audioBuffer], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        
        audioRef.current.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };
      }
    } catch (error) {
      console.error('Error generating voice response:', error);
      setIsSpeaking(false);
    }
  };

  const getPersonaDescription = (persona: string): string => {
    const descriptions = {
      sophia: 'business intelligence and market analysis',
      karen: 'clinical research and pharmaceutical insights',
      cherry: 'creative projects and cross-domain innovation'
    };
    return descriptions[persona] || 'general assistance';
  };

  const getQuickActions = (): QuickAction[] => {
    const baseActions: QuickAction[] = [
      {
        id: 'search',
        label: 'Search',
        icon: <Search className="w-4 h-4" />,
        action: () => setInputValue('Search for ')
      }
    ];

    const personaActions = {
      sophia: [
        {
          id: 'presentation',
          label: 'Create Presentation',
          icon: <Presentation className="w-4 h-4" />,
          action: () => setInputValue('Create a presentation about ')
        },
        {
          id: 'market_analysis',
          label: 'Market Analysis',
          icon: <FileText className="w-4 h-4" />,
          action: () => setInputValue('Analyze the market for ')
        }
      ],
      karen: [
        {
          id: 'research_presentation',
          label: 'Research Presentation',
          icon: <Presentation className="w-4 h-4" />,
          action: () => setInputValue('Create a research presentation on ')
        },
        {
          id: 'clinical_analysis',
          label: 'Clinical Analysis',
          icon: <FileText className="w-4 h-4" />,
          action: () => setInputValue('Analyze clinical data for ')
        }
      ],
      cherry: [
        {
          id: 'create_song',
          label: 'Create Song',
          icon: <Music className="w-4 h-4" />,
          action: () => setInputValue('Create a song about ')
        },
        {
          id: 'create_image',
          label: 'Create Image',
          icon: <Image className="w-4 h-4" />,
          action: () => setInputValue('Create an image of ')
        },
        {
          id: 'create_video',
          label: 'Create Video',
          icon: <Video className="w-4 h-4" />,
          action: () => setInputValue('Create a video about ')
        },
        {
          id: 'write_story',
          label: 'Write Story',
          icon: <FileText className="w-4 h-4" />,
          action: () => setInputValue('Write a story about ')
        }
      ]
    };

    return [...baseActions, ...personaActions[currentPersona]];
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const personaConfig = getPersonaConfig(currentPersona);

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header with Persona Switcher */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center space-x-4">
          <div className="flex space-x-2">
            {(['sophia', 'karen', 'cherry'] as const).map((persona) => (
              <Button
                key={persona}
                variant={currentPersona === persona ? 'default' : 'outline'}
                size="sm"
                onClick={() => handlePersonaSwitch(persona)}
                className={`${currentPersona === persona ? personaConfig.colors.primary : ''}`}
              >
                <Avatar className="w-6 h-6 mr-2">
                  <AvatarFallback className={personaConfig.colors.background}>
                    {persona.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                {persona.charAt(0).toUpperCase() + persona.slice(1)}
              </Button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className={personaConfig.colors.accent}>
            {searchMode.replace('_', ' ').toUpperCase()}
          </Badge>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                >
                  {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {voiceEnabled ? 'Disable Voice' : 'Enable Voice'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-b bg-muted/50">
        <div className="flex flex-wrap gap-2">
          {getQuickActions().map((action) => (
            <Button
              key={action.id}
              variant="outline"
              size="sm"
              onClick={action.action}
              className="flex items-center space-x-2"
            >
              {action.icon}
              <span>{action.label}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.sender === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : `bg-card border ${personaConfig.colors.border}`
                }`}
              >
                {message.sender === 'ai' && (
                  <div className="flex items-center space-x-2 mb-2">
                    <Avatar className="w-6 h-6">
                      <AvatarFallback className={personaConfig.colors.background}>
                        {message.persona.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-sm font-medium">
                      {message.persona.charAt(0).toUpperCase() + message.persona.slice(1)}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {message.type}
                    </Badge>
                  </div>
                )}
                
                <div className="text-sm">{message.content}</div>
                
                {message.metadata && (
                  <div className="mt-2 text-xs text-muted-foreground">
                    {message.type === 'search_results' && (
                      <div>
                        Found {message.metadata.metadata?.total_results} results from {message.metadata.sources?.length} sources
                      </div>
                    )}
                    {message.type === 'presentation' && (
                      <div>
                        Presentation ID: {message.metadata.presentation_id}
                      </div>
                    )}
                  </div>
                )}
                
                <div className="text-xs text-muted-foreground mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-card border rounded-lg p-3 max-w-[80%]">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t bg-card">
        <div className="flex items-center space-x-2">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Message ${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}...`}
              disabled={isLoading}
              className="pr-12"
            />
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleVoiceInput}
                    disabled={isLoading}
                    className={`absolute right-2 top-1/2 transform -translate-y-1/2 ${
                      isListening ? 'text-red-500' : ''
                    }`}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {isListening ? 'Stop Listening' : 'Voice Input'}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className={personaConfig.colors.primary}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Hidden audio element for voice responses */}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
};

export default EnhancedChatInterface;

