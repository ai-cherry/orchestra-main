import React, { useState } from 'react';
import { XMarkIcon, PhotoIcon, VideoCameraIcon, SparklesIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';

interface MultimediaPanelProps {
  onClose: () => void;
}

interface GenerationRequest {
  id: string;
  type: 'image' | 'video';
  prompt: string;
  style: string;
  dimensions: string;
  duration?: number;
  progress: number;
  status: 'pending' | 'generating' | 'completed' | 'error';
  result?: string;
  error?: string;
}

export const MultimediaPanel: React.FC<MultimediaPanelProps> = ({
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'image' | 'video'>('image');
  const [prompt, setPrompt] = useState('');
  const [imageStyle, setImageStyle] = useState('realistic');
  const [imageDimensions, setImageDimensions] = useState('1024x1024');
  const [videoStyle, setVideoStyle] = useState('cinematic');
  const [videoDimensions, setVideoDimensions] = useState('1920x1080');
  const [videoDuration, setVideoDuration] = useState(5);
  const [generations, setGenerations] = useState<GenerationRequest[]>([]);

  const imageStyles = [
    { id: 'realistic', name: 'Realistic', description: 'Photorealistic style' },
    { id: 'artistic', name: 'Artistic', description: 'Artistic and creative' },
    { id: 'anime', name: 'Anime', description: 'Anime/manga style' },
    { id: 'cartoon', name: 'Cartoon', description: 'Cartoon illustration' },
    { id: 'oil-painting', name: 'Oil Painting', description: 'Classic oil painting' },
    { id: 'watercolor', name: 'Watercolor', description: 'Watercolor painting' },
    { id: 'digital-art', name: 'Digital Art', description: 'Modern digital art' },
    { id: 'sketch', name: 'Sketch', description: 'Pencil sketch style' },
  ];

  const videoStyles = [
    { id: 'cinematic', name: 'Cinematic', description: 'Movie-like quality' },
    { id: 'documentary', name: 'Documentary', description: 'Documentary style' },
    { id: 'animation', name: 'Animation', description: 'Animated content' },
    { id: 'timelapse', name: 'Time-lapse', description: 'Time-lapse effect' },
    { id: 'slowmotion', name: 'Slow Motion', description: 'Slow motion effect' },
  ];

  const imageDimensionOptions = [
    '512x512', '768x768', '1024x1024', '1216x832', '832x1216',
    '1344x768', '768x1344', '1536x640', '640x1536'
  ];

  const videoDimensionOptions = [
    '1280x720', '1920x1080', '2560x1440', '3840x2160'
  ];

  const simulateGeneration = async (request: GenerationRequest) => {
    // Update status to generating
    setGenerations(prev => prev.map(g => 
      g.id === request.id ? { ...g, status: 'generating' } : g
    ));

    // Simulate progress
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise(resolve => setTimeout(resolve, request.type === 'video' ? 500 : 300));
      setGenerations(prev => prev.map(g => 
        g.id === request.id ? { ...g, progress } : g
      ));
    }

    // Complete with mock result
    const mockResult = request.type === 'image' 
      ? 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNGVjZGM0IiAvPgogIDx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+R2VuZXJhdGVkIEltYWdlPC90ZXh0Pgo8L3N2Zz4='
      : '#';

    setGenerations(prev => prev.map(g => 
      g.id === request.id ? { 
        ...g, 
        status: 'completed', 
        progress: 100, 
        result: mockResult 
      } : g
    ));
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    const newRequest: GenerationRequest = {
      id: `gen-${Date.now()}`,
      type: activeTab,
      prompt: prompt.trim(),
      style: activeTab === 'image' ? imageStyle : videoStyle,
      dimensions: activeTab === 'image' ? imageDimensions : videoDimensions,
      duration: activeTab === 'video' ? videoDuration : undefined,
      progress: 0,
      status: 'pending'
    };

    setGenerations(prev => [newRequest, ...prev]);
    setPrompt('');

    // Start generation
    await simulateGeneration(newRequest);
  };

  const removeGeneration = (id: string) => {
    setGenerations(prev => prev.filter(g => g.id !== id));
  };

  const getStatusColor = (status: GenerationRequest['status']) => {
    switch (status) {
      case 'pending': return 'text-blue-400';
      case 'generating': return 'text-yellow-400';
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-white';
    }
  };

  return (
    <div className="w-full bg-white/5 rounded-xl border border-white/10 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-white mb-1">Multimedia Generation</h3>
          <p className="text-white/70 text-sm">
            Create stunning images and videos using AI
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          <XMarkIcon className="w-5 h-5 text-white/70" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('image')}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
            ${activeTab === 'image' 
              ? 'bg-blue-500 text-white' 
              : 'bg-white/10 text-white/70 hover:bg-white/20'
            }
          `}
        >
          <PhotoIcon className="w-5 h-5" />
          Image Generation
        </button>
        <button
          onClick={() => setActiveTab('video')}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
            ${activeTab === 'video' 
              ? 'bg-blue-500 text-white' 
              : 'bg-white/10 text-white/70 hover:bg-white/20'
            }
          `}
        >
          <VideoCameraIcon className="w-5 h-5" />
          Video Generation
        </button>
      </div>

      {/* Generation Form */}
      <div className="space-y-6 mb-6">
        {/* Prompt Input */}
        <div>
          <label className="block text-white font-medium mb-2">
            <SparklesIcon className="w-5 h-5 inline mr-2" />
            Describe what you want to create
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={activeTab === 'image' 
              ? 'A beautiful sunset over a mountain landscape...'
              : 'A time-lapse of a flower blooming...'
            }
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/60 resize-none focus:border-white/40 focus:bg-white/15 transition-colors"
            rows={3}
          />
        </div>

        {/* Style Selection */}
        <div>
          <label className="block text-white font-medium mb-3">
            <AdjustmentsHorizontalIcon className="w-5 h-5 inline mr-2" />
            Style
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(activeTab === 'image' ? imageStyles : videoStyles).map((style) => (
              <button
                key={style.id}
                onClick={() => activeTab === 'image' ? setImageStyle(style.id) : setVideoStyle(style.id)}
                className={`
                  p-3 rounded-lg border-2 text-left transition-all
                  ${(activeTab === 'image' ? imageStyle : videoStyle) === style.id
                    ? 'border-blue-500 bg-blue-500/20 text-white'
                    : 'border-white/20 bg-white/5 text-white/80 hover:border-white/40'
                  }
                `}
              >
                <div className="font-medium">{style.name}</div>
                <div className="text-xs text-white/60 mt-1">{style.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Dimensions and Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-white font-medium mb-2">
              {activeTab === 'image' ? 'Image Size' : 'Video Resolution'}
            </label>
            <select
              value={activeTab === 'image' ? imageDimensions : videoDimensions}
              onChange={(e) => activeTab === 'image' 
                ? setImageDimensions(e.target.value) 
                : setVideoDimensions(e.target.value)
              }
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:border-white/40"
            >
              {(activeTab === 'image' ? imageDimensionOptions : videoDimensionOptions).map((size) => (
                <option key={size} value={size} className="bg-gray-800">
                  {size}
                </option>
              ))}
            </select>
          </div>

          {activeTab === 'video' && (
            <div>
              <label className="block text-white font-medium mb-2">
                Duration (seconds)
              </label>
              <select
                value={videoDuration}
                onChange={(e) => setVideoDuration(Number(e.target.value))}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:border-white/40"
              >
                <option value={3} className="bg-gray-800">3 seconds</option>
                <option value={5} className="bg-gray-800">5 seconds</option>
                <option value={10} className="bg-gray-800">10 seconds</option>
                <option value={15} className="bg-gray-800">15 seconds</option>
                <option value={30} className="bg-gray-800">30 seconds</option>
              </select>
            </div>
          )}
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={!prompt.trim()}
          className="w-full px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
        >
          <SparklesIcon className="w-6 h-6 inline mr-2" />
          Generate {activeTab === 'image' ? 'Image' : 'Video'}
        </button>
      </div>

      {/* Generation History */}
      {generations.length > 0 && (
        <div>
          <h4 className="font-medium text-white mb-4">
            Recent Generations ({generations.length})
          </h4>
          
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {generations.map((generation) => (
              <div
                key={generation.id}
                className="flex gap-4 p-4 bg-white/5 rounded-lg border border-white/10"
              >
                {/* Preview */}
                <div className="flex-shrink-0 w-16 h-16 bg-white/10 rounded-lg flex items-center justify-center">
                  {generation.status === 'completed' && generation.result && generation.type === 'image' ? (
                    <img 
                      src={generation.result} 
                      alt="Generated" 
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : generation.type === 'image' ? (
                    <PhotoIcon className="w-8 h-8 text-white/40" />
                  ) : (
                    <VideoCameraIcon className="w-8 h-8 text-white/40" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-white text-sm">
                        {generation.type === 'image' ? '🖼️' : '🎬'} {generation.style} {generation.type}
                      </div>
                      <div className="text-white/60 text-sm mt-1 line-clamp-2">
                        "{generation.prompt}"
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-white/50">
                        <span>{generation.dimensions}</span>
                        {generation.duration && <span>{generation.duration}s</span>}
                        <span className={getStatusColor(generation.status)}>
                          {generation.status}
                        </span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => removeGeneration(generation.id)}
                      className="p-1 hover:bg-white/10 rounded transition-colors"
                    >
                      <XMarkIcon className="w-4 h-4 text-white/60" />
                    </button>
                  </div>

                  {/* Progress Bar */}
                  {generation.status === 'generating' && (
                    <div className="mt-3 w-full bg-white/20 rounded-full h-2">
                      <div
                        className="h-2 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full transition-all duration-300"
                        style={{ width: `${generation.progress}%` }}
                      />
                    </div>
                  )}

                  {/* Actions */}
                  {generation.status === 'completed' && generation.result && (
                    <div className="flex gap-2 mt-3">
                      <button className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors">
                        Download
                      </button>
                      <button className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-xs hover:bg-green-500/30 transition-colors">
                        Use in Chat
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Panel */}
      <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
        <h5 className="font-medium text-purple-400 mb-2">Generation Tips:</h5>
        <ul className="text-sm text-purple-300 space-y-1">
          <li>• Be specific and descriptive in your prompts</li>
          <li>• Include details about lighting, mood, and composition</li>
          <li>• {activeTab === 'image' ? 'Higher resolutions take longer to generate' : 'Longer videos require more processing time'}</li>
          <li>• Generated content can be used directly in conversations</li>
        </ul>
      </div>
    </div>
  );
}; 