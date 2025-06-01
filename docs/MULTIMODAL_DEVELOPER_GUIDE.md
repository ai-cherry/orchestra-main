# Multimodal OmniSearch Developer Guide

## Quick Start

### 1. Environment Setup
```bash
# Add to .env
PORTKEY_API_KEY=your_portkey_api_key
ENABLE_IMAGE_GEN=true
ENABLE_VIDEO_SYNTH=true
ENABLE_ADVANCED_SEARCH=true

# Install dependencies
npm install @portkey-ai/portkey-node
npm install ffmpeg.js
npm install sharp
```

### 2. Basic Implementation

#### Image Generation Example
```typescript
import { PortkeyService } from '@/services/portkey/PortkeyService';

const generateImage = async (prompt: string) => {
  const portkey = new PortkeyService();
  
  try {
    const result = await portkey.generateImage(prompt, {
      size: '1024x1024',
      quality: 'hd'
    });
    
    return {
      url: result.data[0].url,
      revisedPrompt: result.data[0].revised_prompt
    };
  } catch (error) {
    console.error('Image generation failed:', error);
    throw error;
  }
};
```

#### Video Synthesis Example
```typescript
import { VideoSynthesizer } from '@/services/video/VideoSynthesizer';

const createVideo = async (topic: string) => {
  const synthesizer = new VideoSynthesizer();
  
  // Generate script
  const script = await synthesizer.generateScript(topic);
  
  // Fetch media assets
  const assets = await synthesizer.fetchMediaAssets(script.keywords);
  
  // Render video
  const videoUrl = await synthesizer.renderVideo(script, assets);
  
  return videoUrl;
};
```

## Component Templates

### 1. Multimodal Search Input
```tsx
const MultimodalSearchInput: React.FC = () => {
  const [query, setQuery] = useState('');
  const [modality, setModality] = useState<SearchModality>('auto');
  
  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search, generate images, or create videos..."
        className="w-full px-4 py-2 pr-24 rounded-lg border"
      />
      
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-2">
        <ModalityToggle value={modality} onChange={setModality} />
        <SearchButton onClick={() => handleSearch(query, modality)} />
      </div>
    </div>
  );
};
```

### 2. Media Result Card
```tsx
interface MediaResultProps {
  type: 'image' | 'video';
  url: string;
  metadata: MediaMetadata;
}

const MediaResultCard: React.FC<MediaResultProps> = ({ type, url, metadata }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {type === 'image' ? (
        <img src={url} alt={metadata.alt} className="w-full h-48 object-cover" />
      ) : (
        <video src={url} controls className="w-full h-48" />
      )}
      
      <div className="p-4">
        <h3 className="font-semibold">{metadata.title}</h3>
        <p className="text-sm text-gray-600">{metadata.description}</p>
        
        <div className="mt-2 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Generated {formatRelativeTime(metadata.createdAt)}
          </span>
          <MediaActions url={url} type={type} />
        </div>
      </div>
    </div>
  );
};
```

## API Reference

### PortkeyService Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `generateImage` | `prompt: string, options?: ImageOptions` | `Promise<ImageResult>` | Generate image using DALL-E 3 |
| `generateText` | `prompt: string, model?: string` | `Promise<TextResult>` | Generate text using GPT-4 |
| `checkUsage` | `service: string` | `Promise<UsageStats>` | Check API usage and limits |

### VideoSynthesizer Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `generateScript` | `topic: string` | `Promise<VideoScript>` | Generate video script |
| `fetchMediaAssets` | `keywords: string[]` | `Promise<MediaAsset[]>` | Fetch stock media |
| `renderVideo` | `script: VideoScript, assets: MediaAsset[]` | `Promise<string>` | Render final video |

## State Management

### Task Queue Store
```typescript
interface TaskQueueState {
  tasks: Task[];
  activeTask: Task | null;
  addTask: (type: TaskType, prompt: string) => string;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;
  getTaskById: (id: string) => Task | undefined;
}

// Usage
const { addTask, tasks } = useTaskQueue();
const taskId = addTask('image', 'Generate sunset landscape');
```

### Media Cache Store
```typescript
interface MediaCacheState {
  items: Map<string, CachedMedia>;
  get: (key: string) => CachedMedia | null;
  set: (key: string, media: MediaData) => void;
  has: (key: string) => boolean;
  clear: () => void;
}

// Usage
const cache = useMediaCache();
const cached = cache.get(promptHash);
if (!cached) {
  const result = await generateImage(prompt);
  cache.set(promptHash, result);
}
```

## Error Handling

### Common Error Scenarios
```typescript
enum MultimodalError {
  RATE_LIMIT = 'RATE_LIMIT',
  CONTENT_POLICY = 'CONTENT_POLICY',
  INVALID_PROMPT = 'INVALID_PROMPT',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  INSUFFICIENT_CREDITS = 'INSUFFICIENT_CREDITS'
}

const handleMultimodalError = (error: any) => {
  switch (error.code) {
    case MultimodalError.RATE_LIMIT:
      return 'Please wait a moment before trying again';
    case MultimodalError.CONTENT_POLICY:
      return 'Your request violates content policy';
    case MultimodalError.INSUFFICIENT_CREDITS:
      return 'API credits exhausted for today';
    default:
      return 'An unexpected error occurred';
  }
};
```

## Performance Optimization

### 1. Debouncing
```typescript
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    handleSearch(query);
  }, 500),
  []
);
```

### 2. Lazy Loading
```tsx
const MediaGallery = lazy(() => import('@/components/MediaGallery'));

<Suspense fallback={<MediaGallerySkeleton />}>
  <MediaGallery items={results} />
</Suspense>
```

### 3. Virtual Scrolling
```tsx
import { FixedSizeList } from 'react-window';

const VirtualMediaList: React.FC<{ items: Media[] }> = ({ items }) => (
  <FixedSizeList
    height={600}
    itemCount={items.length}
    itemSize={200}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        <MediaResultCard {...items[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

## Testing Utilities

### Mock Generators
```typescript
export const mockImageResult = (overrides?: Partial<ImageResult>): ImageResult => ({
  url: 'https://example.com/generated-image.jpg',
  revisedPrompt: 'A beautiful sunset over mountains',
  createdAt: new Date().toISOString(),
  ...overrides
});

export const mockVideoResult = (overrides?: Partial<VideoResult>): VideoResult => ({
  url: 'https://example.com/generated-video.mp4',
  duration: 30,
  script: 'Sample video script',
  assets: [],
  ...overrides
});
```

### Test Helpers
```typescript
export const waitForGeneration = async (taskId: string) => {
  await waitFor(() => {
    const task = screen.getByTestId(`task-${taskId}`);
    expect(task).toHaveAttribute('data-status', 'completed');
  });
};

export const simulateImageUpload = async (file: File) => {
  const input = screen.getByLabelText('Upload image');
  await userEvent.upload(input, file);
};
```

## Deployment Checklist

- [ ] Environment variables configured
- [ ] API keys secured in vault
- [ ] Rate limiting implemented
- [ ] Cost monitoring enabled
- [ ] Error boundaries in place
- [ ] Fallback UI components ready
- [ ] Cache warming strategy defined
- [ ] A/B testing flags configured
- [ ] Analytics tracking enabled
- [ ] Performance monitoring active

## Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Solution: Implement exponential backoff
   - Cache results aggressively
   - Use queue prioritization

2. **Large Media Files**
   - Solution: Implement streaming uploads
   - Use progressive image loading
   - Compress media before caching

3. **Memory Leaks**
   - Solution: Clear task queue periodically
   - Implement cache eviction policy
   - Use weak references for large objects

## Resources

- [Portkey Documentation](https://docs.portkey.ai)
- [DALL-E 3 API Reference](https://platform.openai.com/docs/guides/images)
- [FFmpeg.js Guide](https://github.com/ffmpegwasm/ffmpeg.wasm)
- [React Flow Examples](https://reactflow.dev/examples) 