import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import useOrchestratorStore from '../../../store/orchestratorStore';
import { orchestratorService } from '../../../services/orchestratorService';

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionError extends Event {
  error: string;
  message?: string;
}

// Extend Window interface for webkit prefix
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export const VoiceRecorder: React.FC = () => {
  const [isSupported, setIsSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const {
    isRecording,
    transcription,
    startRecording,
    stopRecording,
    setTranscription,
    setAudioBlob,
    setSearchQuery,
  } = useOrchestratorStore();

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setError(null);
      console.log('Speech recognition started');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      const currentTranscript = transcription + finalTranscript;
      setTranscription(currentTranscript + interimTranscript);
    };

    recognition.onerror = (event: SpeechRecognitionError) => {
      console.error('Speech recognition error:', event.error);
      
      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow microphone access and try again.');
        setPermissionGranted(false);
      } else if (event.error === 'no-speech') {
        setError('No speech detected. Please try again.');
      } else {
        setError(`Speech recognition error: ${event.error}`);
      }
      
      stopRecording();
    };

    recognition.onend = () => {
      console.log('Speech recognition ended');
      if (isRecording) {
        // Restart if still recording
        recognition.start();
      }
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isSupported, isRecording, transcription, setTranscription, stopRecording]);

  // Initialize audio recording
  const startAudioRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermissionGranted(true);
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        
        // Send to transcription service
        try {
          const result = await orchestratorService.transcribeAudio(audioBlob);
          if (result.text && !transcription) {
            setTranscription(result.text);
          }
        } catch (error) {
          console.error('Transcription service error:', error);
        }
      };

      mediaRecorder.start();
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Failed to access microphone. Please check your permissions.');
      setPermissionGranted(false);
    }
  }, [setAudioBlob, transcription, setTranscription]);

  const handleStartRecording = useCallback(() => {
    if (!isSupported) return;

    setTranscription('');
    startRecording();
    
    // Start speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
    
    // Start audio recording
    startAudioRecording();
  }, [isSupported, startRecording, setTranscription, startAudioRecording]);

  const handleStopRecording = useCallback(() => {
    stopRecording();
    
    // Stop speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    // Stop audio recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    // Set the transcription as search query
    if (transcription.trim()) {
      setSearchQuery(transcription.trim());
    }
  }, [stopRecording, transcription, setSearchQuery]);

  const handleToggleRecording = () => {
    if (isRecording) {
      handleStopRecording();
    } else {
      handleStartRecording();
    }
  };

  if (!isSupported) {
    return (
      <Card className="p-4 bg-red-900/20 border-red-800">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center">
        <Button
          onClick={handleToggleRecording}
          className={`
            relative w-20 h-20 rounded-full transition-all duration-300
            ${isRecording 
              ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-600/50' 
              : 'bg-gray-700 hover:bg-gray-600'
            }
          `}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {isRecording ? (
            <>
              <MicOff className="w-8 h-8 text-white" />
              <span className="absolute inset-0 rounded-full animate-ping bg-red-600 opacity-75" />
            </>
          ) : (
            <Mic className="w-8 h-8 text-white" />
          )}
        </Button>
      </div>

      {isRecording && (
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-400">Recording...</span>
          </div>
          {transcription && (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-300">{transcription}</p>
            </div>
          )}
        </div>
      )}

      {error && (
        <Card className="p-4 bg-red-900/20 border-red-800">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {!permissionGranted && !isRecording && (
        <p className="text-xs text-gray-500 text-center">
          Click the microphone to start recording. You may need to grant microphone permissions.
        </p>
      )}
    </div>
  );
};
