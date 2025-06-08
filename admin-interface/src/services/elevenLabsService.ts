import { ElevenLabsClient } from 'elevenlabs';

interface VoiceConfig {
  voiceId: string;
  model: 'eleven_v3' | 'eleven_turbo_v2_5' | 'eleven_multilingual_v2';
  stability: number;
  similarityBoost: number;
  style: number;
  useSpeakerBoost: boolean;
}

interface AudioTag {
  tag: string;
  intensity: number;
}

class ElevenLabsService {
  private client: ElevenLabsClient;
  private apiKey = 'sk_c6b8e5b5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5'; // User's API key

  constructor() {
    this.client = new ElevenLabsClient({
      apiKey: this.apiKey
    });
  }

  // Enhanced voice generation with Eleven v3 features
  async generateSpeech(
    text: string,
    persona: 'sophia' | 'karen' | 'cherry',
    options?: {
      audioTags?: AudioTag[];
      dialogueMode?: boolean;
      emotion?: 'neutral' | 'excited' | 'sorrowful' | 'confident' | 'friendly';
      language?: string;
    }
  ): Promise<ArrayBuffer> {
    const voiceConfig = this.getPersonaVoiceConfig(persona);
    
    // Apply Eleven v3 audio tags for enhanced expressiveness
    const enhancedText = this.applyAudioTags(text, options?.audioTags, options?.emotion);
    
    try {
      const audio = await this.client.generate({
        voice: voiceConfig.voiceId,
        model_id: voiceConfig.model,
        text: enhancedText,
        voice_settings: {
          stability: voiceConfig.stability,
          similarity_boost: voiceConfig.similarityBoost,
          style: voiceConfig.style,
          use_speaker_boost: voiceConfig.useSpeakerBoost
        },
        language_code: options?.language || 'en'
      });

      return audio;
    } catch (error) {
      console.error('ElevenLabs generation error:', error);
      throw error;
    }
  }

  // Multi-speaker dialogue generation (Eleven v3 feature)
  async generateDialogue(
    speakers: Array<{
      persona: 'sophia' | 'karen' | 'cherry';
      text: string;
      emotion?: string;
    }>
  ): Promise<ArrayBuffer> {
    try {
      const dialogueText = speakers.map((speaker, index) => {
        const voiceConfig = this.getPersonaVoiceConfig(speaker.persona);
        const emotion = speaker.emotion ? `[${speaker.emotion.toUpperCase()}]` : '';
        return `<voice name="${voiceConfig.voiceId}">${emotion}${speaker.text}</voice>`;
      }).join('\n');

      const audio = await this.client.generate({
        voice: 'dialogue', // Special dialogue voice ID
        model_id: 'eleven_v3',
        text: dialogueText,
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.8,
          style: 0.7,
          use_speaker_boost: true
        }
      });

      return audio;
    } catch (error) {
      console.error('ElevenLabs dialogue generation error:', error);
      throw error;
    }
  }

  // Real-time voice streaming for chat interface
  async streamSpeech(
    text: string,
    persona: 'sophia' | 'karen' | 'cherry',
    onChunk: (chunk: ArrayBuffer) => void
  ): Promise<void> {
    const voiceConfig = this.getPersonaVoiceConfig(persona);
    
    try {
      const stream = await this.client.generate({
        voice: voiceConfig.voiceId,
        model_id: voiceConfig.model,
        text: text,
        stream: true,
        voice_settings: {
          stability: voiceConfig.stability,
          similarity_boost: voiceConfig.similarityBoost,
          style: voiceConfig.style,
          use_speaker_boost: voiceConfig.useSpeakerBoost
        }
      });

      // Handle streaming chunks
      for await (const chunk of stream) {
        onChunk(chunk);
      }
    } catch (error) {
      console.error('ElevenLabs streaming error:', error);
      throw error;
    }
  }

  // Voice cloning for personalized experience
  async cloneVoice(audioFile: File, name: string): Promise<string> {
    try {
      const voice = await this.client.voices.add({
        name: name,
        files: [audioFile],
        description: `Custom voice for ${name}`
      });

      return voice.voice_id;
    } catch (error) {
      console.error('Voice cloning error:', error);
      throw error;
    }
  }

  // Speech-to-text for voice input
  async transcribeAudio(audioBlob: Blob): Promise<string> {
    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'audio.wav', { type: 'audio/wav' });
      
      // Use Web Speech API as fallback since ElevenLabs doesn't have STT
      return new Promise((resolve, reject) => {
        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          resolve(transcript);
        };

        recognition.onerror = (event: any) => {
          reject(new Error(`Speech recognition error: ${event.error}`));
        };

        recognition.start();
      });
    } catch (error) {
      console.error('Speech transcription error:', error);
      throw error;
    }
  }

  private getPersonaVoiceConfig(persona: string): VoiceConfig {
    const configs = {
      sophia: {
        voiceId: 'EXAVITQu4vr4xnSDxMaL', // Professional female voice
        model: 'eleven_v3' as const,
        stability: 0.7,
        similarityBoost: 0.8,
        style: 0.6,
        useSpeakerBoost: true
      },
      karen: {
        voiceId: 'ErXwobaYiN019PkySvjV', // Authoritative female voice
        model: 'eleven_v3' as const,
        stability: 0.8,
        similarityBoost: 0.9,
        style: 0.4,
        useSpeakerBoost: true
      },
      cherry: {
        voiceId: 'MF3mGyEYCl7XYWbV9V6O', // Friendly, creative voice
        model: 'eleven_v3' as const,
        stability: 0.5,
        similarityBoost: 0.7,
        style: 0.8,
        useSpeakerBoost: true
      }
    };

    return configs[persona] || configs.cherry;
  }

  private applyAudioTags(
    text: string,
    audioTags?: AudioTag[],
    emotion?: string
  ): string {
    let enhancedText = text;

    // Apply emotion tags (Eleven v3 feature)
    if (emotion) {
      enhancedText = `[${emotion.toUpperCase()}] ${enhancedText}`;
    }

    // Apply custom audio tags
    if (audioTags && audioTags.length > 0) {
      const tags = audioTags.map(tag => `[${tag.tag}:${tag.intensity}]`).join(' ');
      enhancedText = `${tags} ${enhancedText}`;
    }

    return enhancedText;
  }

  // Get available voices for persona customization
  async getAvailableVoices(): Promise<any[]> {
    try {
      const voices = await this.client.voices.getAll();
      return voices.voices;
    } catch (error) {
      console.error('Error fetching voices:', error);
      return [];
    }
  }

  // Voice settings optimization
  async optimizeVoiceSettings(
    voiceId: string,
    sampleText: string
  ): Promise<VoiceConfig> {
    // This would use ElevenLabs' voice optimization API
    // For now, return default optimized settings
    return {
      voiceId,
      model: 'eleven_v3',
      stability: 0.7,
      similarityBoost: 0.8,
      style: 0.6,
      useSpeakerBoost: true
    };
  }
}

export default ElevenLabsService;

