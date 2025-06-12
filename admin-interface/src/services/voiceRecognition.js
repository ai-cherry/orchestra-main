export class VoiceRecognitionService {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.isSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    this.initRecognition();
  }
  
  initRecognition() {
    if (!this.isSupported) return;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;
  }
  
  async startListening(onResult, onError, onEnd) {
    if (!this.isSupported || !this.recognition) {
      onError('Speech recognition not supported in this browser');
      return false;
    }
    
    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('');
        
      if (event.results[0].isFinal) {
        onResult(transcript);
      }
    };
    
    this.recognition.onerror = (event) => onError(event.error);
    this.recognition.onend = () => {
      this.isListening = false;
      onEnd();
    };
    
    try {
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (error) {
      onError(error.message);
      return false;
    }
  }
  
  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }
  
  // Check if browser supports speech recognition
  static isSupported() {
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
  }
  
  // Get supported languages (basic implementation)
  static getSupportedLanguages() {
    return [
      { code: 'en-US', name: 'English (US)' },
      { code: 'en-GB', name: 'English (UK)' },
      { code: 'es-ES', name: 'Spanish' },
      { code: 'fr-FR', name: 'French' },
      { code: 'de-DE', name: 'German' },
      { code: 'it-IT', name: 'Italian' },
      { code: 'pt-BR', name: 'Portuguese (Brazil)' },
      { code: 'ja-JP', name: 'Japanese' },
      { code: 'ko-KR', name: 'Korean' },
      { code: 'zh-CN', name: 'Chinese (Simplified)' }
    ];
  }
  
  // Set language for recognition
  setLanguage(languageCode) {
    if (this.recognition) {
      this.recognition.lang = languageCode;
    }
  }
  
  // Set continuous mode
  setContinuous(continuous) {
    if (this.recognition) {
      this.recognition.continuous = continuous;
    }
  }
  
  // Set interim results
  setInterimResults(interimResults) {
    if (this.recognition) {
      this.recognition.interimResults = interimResults;
    }
  }
} 