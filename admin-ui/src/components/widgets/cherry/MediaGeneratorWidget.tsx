import React, { useState } from 'react';
import { Image, Video, Music, Sparkles, Loader2 } from 'lucide-react';
import { getPortkeyService } from '@/services/portkey/PortkeyService';

interface MediaGeneratorWidgetProps {
  api?: string;
}

interface MediaGeneration {
  id: number;
  type: 'image' | 'video' | 'audio';
  title: string;
  time: string;
  url?: string;
  error?: string;
}

const MediaGeneratorWidget: React.FC<MediaGeneratorWidgetProps> = ({ api = 'Portkey' }) => {
  const [selectedType, setSelectedType] = useState<'image' | 'video' | 'audio'>('image');
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generations, setGenerations] = useState<MediaGeneration[]>([
    { id: 1, type: 'image', title: 'Sunset landscape', time: '2 hours ago' },
    { id: 2, type: 'video', title: 'Birthday greeting', time: '1 day ago' },
    { id: 3, type: 'audio', title: 'Relaxation music', time: '3 days ago' },
  ]);
  
  const mediaTypes = [
    { type: 'image' as const, icon: Image, label: 'Images' },
    { type: 'video' as const, icon: Video, label: 'Videos' },
    { type: 'audio' as const, icon: Music, label: 'Audio' },
  ];

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    setError(null);
    
    try {
      const portkey = getPortkeyService();
      
      if (selectedType === 'image') {
        const result = await portkey.generateImage(prompt, {
          size: '1024x1024',
          quality: 'standard',
          style: 'vivid'
        });
        
        if (result.success && result.data?.[0]) {
          const newGeneration: MediaGeneration = {
            id: Date.now(),
            type: 'image',
            title: prompt.slice(0, 30) + (prompt.length > 30 ? '...' : ''),
            time: 'Just now',
            url: result.data[0].url
          };
          setGenerations([newGeneration, ...generations.slice(0, 9)]);
          setPrompt('');
        }
      } else if (selectedType === 'video') {
        // Video generation not yet implemented
        setError('Video generation coming soon!');
      } else if (selectedType === 'audio') {
        // Audio generation not yet implemented
        setError('Audio generation coming soon!');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate media');
      console.error('Generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Media Generator</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">Powered by {api}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-6">
        {mediaTypes.map(({ type, icon: Icon, label }) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`p-3 rounded-lg border-2 transition-all ${
              selectedType === type
                ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <Icon className={`h-6 w-6 mx-auto mb-1 ${
              selectedType === type ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400'
            }`} />
            <p className={`text-xs ${
              selectedType === type ? 'text-red-700 dark:text-red-300 font-medium' : 'text-gray-600 dark:text-gray-400'
            }`}>
              {label}
            </p>
          </button>
        ))}
      </div>

      <div className="bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-2 mb-3">
          <Sparkles className="h-5 w-5 text-red-600 dark:text-red-400" />
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Quick Generate</span>
        </div>
        <input
          type="text"
          placeholder={`Describe the ${selectedType} you want to create...`}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !isGenerating && handleGenerate()}
          disabled={isGenerating}
          className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent disabled:opacity-50"
        />
        {error && (
          <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>
        )}
        <button 
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="mt-3 w-full px-4 py-2 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 text-white rounded-md text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <span>Generate {selectedType.charAt(0).toUpperCase() + selectedType.slice(1)}</span>
          )}
        </button>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Recent Creations</h4>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {generations.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
              <div className="flex items-center space-x-3">
                {item.type === 'image' && <Image className="h-4 w-4 text-purple-500" />}
                {item.type === 'video' && <Video className="h-4 w-4 text-blue-500" />}
                {item.type === 'audio' && <Music className="h-4 w-4 text-green-500" />}
                <div>
                  <p className="text-sm text-gray-900 dark:text-gray-100">{item.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{item.time}</p>
                </div>
              </div>
              {item.url ? (
                <a 
                  href={item.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-red-600 dark:text-red-400 hover:underline"
                >
                  View
                </a>
              ) : (
                <button className="text-xs text-red-600 dark:text-red-400 hover:underline">
                  View
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MediaGeneratorWidget; 