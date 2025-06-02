# Testing Orchestrator Phase 3 Features

## Quick Start

1. **Start the development server:**
   ```bash
   cd admin-ui
   pnpm dev
   ```

2. **Navigate to the Orchestrator page:**
   - Open http://localhost:5173/orchestrator
   - You should see the enhanced landing page with tabs

## Feature Testing Guide

### 1. Voice Recording (Chrome/Edge recommended)
- Click the microphone icon in the input mode selector
- Click the large red microphone button to start recording
- Speak clearly - you'll see real-time transcription
- Click the button again to stop recording
- The transcription will populate the search query

### 2. File Upload
- Click the file icon in the input mode selector
- Either:
  - Drag and drop files onto the upload area
  - Click to browse and select files
- Supported formats: Text, PDF, JSON, XML, Images, Audio, Video
- Maximum file size: 50MB

### 3. File Progress Monitoring
- Switch to the "Files" tab
- Upload multiple files to see the progress table
- Watch progress bars update in real-time
- Try canceling an upload or removing completed files

### 4. Voice Synthesis
- Perform a text search first to get results
- Switch to the "Voice Synthesis" tab
- Select a voice (browser voices or premium options)
- Adjust volume, speed, and pitch sliders
- Click "Play" to hear the search results
- Try pause/resume functionality
- Download the synthesized audio

### 5. WebSocket Connection
- Check the connection indicator in the top-right
- Green dot = connected, Red dot = disconnected
- Try disconnecting your network to test reconnection

## Browser Compatibility

### Full Support (All Features)
- Chrome 90+
- Edge 90+

### Partial Support (Limited Voice Features)
- Firefox 80+ (Speech synthesis only)
- Safari 14+ (May require permissions)

### Mobile Testing
- iOS Safari: Voice features require user interaction
- Chrome Android: Full voice support
- Test responsive design on various screen sizes

## Common Issues & Solutions

### Voice Recording Not Working
1. Check browser compatibility
2. Ensure microphone permissions are granted
3. Check if another app is using the microphone
4. Try refreshing the page

### File Upload Issues
1. Check file size (max 50MB)
2. Verify file type is supported
3. Check browser console for errors
4. Ensure sufficient disk space

### WebSocket Connection Issues
1. Check if backend server is running
2. Verify WebSocket URL in environment
3. Check firewall/proxy settings
4. Look for errors in browser console

## Performance Testing

### Large File Uploads
- Try uploading a 40-50MB file
- Monitor memory usage in browser dev tools
- Check if UI remains responsive

### Multiple Concurrent Operations
- Upload multiple files simultaneously
- Record voice while files are uploading
- Switch between tabs during operations

### Voice Synthesis Load
- Generate speech for long text results
- Try different voices and settings
- Monitor CPU usage

## Accessibility Testing

### Keyboard Navigation
- Tab through all interactive elements
- Use Space/Enter to activate buttons
- Escape to close modals/dropdowns

### Screen Reader
- Enable screen reader (NVDA/JAWS/VoiceOver)
- Verify all elements have proper labels
- Check announcement of state changes

### High Contrast Mode
- Enable high contrast in OS settings
- Verify all UI elements remain visible
- Check focus indicators

## Developer Tools

### Debugging WebSocket
```javascript
// In browser console
window.websocketManager = websocketManager;
websocketManager.isConnected(); // Check connection
websocketManager.emit('test', { data: 'test' }); // Send test event
```

### Monitoring Store State
```javascript
// In browser console
const store = useOrchestratorStore.getState();
console.log(store); // View entire state
store.uploads; // Check file uploads
store.isWebSocketConnected; // Check connection
```

### Testing File Progress
```javascript
// Simulate file progress updates
const store = useOrchestratorStore.getState();
const fileId = 'test-file-123';
store.addUpload(new File(['test'], 'test.txt'));
store.updateUploadProgress(fileId, 50);
store.updateUploadStatus(fileId, 'completed');
```

## Next Steps

After testing all features:
1. Document any bugs found
2. Note performance bottlenecks
3. Suggest UI/UX improvements
4. Test with real backend integration