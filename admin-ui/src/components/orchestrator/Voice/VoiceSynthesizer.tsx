import React, { useState, useEffect, useCallback, useRef } from 'react';
import { VolumeX, Play, Pause, Download } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card } from '../../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Slider } from '../../ui/slider';
import useOrchestratorStore from '../../../store/orchestratorStore';
import { orchestratorService } from '../../../services/orchestratorService';

interface Voice {
  id: string;
  name: string;
  lang: string;
  localService?: boolean;
  voiceURI?: string;
}

export const VoiceSynthesizer: React.FC = () => {
  const [isSupported, setIsSupported] = useState(true);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [volume, setVolume] = useState(1);
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const {
    selectedVoice,
    setSelectedVoice,
    setAvailableVoices,
    searchResults,
  } = useOrchestratorStore();

  // Check browser support
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
      return;
    }

    // Load available voices
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      const voiceList: Voice[] = availableVoices.map(voice => ({
        id: voice.voiceURI,
        name: voice.name,
        lang: voice.lang,
        localService: voice.localService,
        voiceURI: voice.voiceURI,
      }));

      // Filter for English voices and add custom options
      const englishVoices = voiceList.filter(voice => voice.lang.startsWith('en'));
      
      // Add custom voice options (these would use the API)
      const customVoices: Voice[] = [
        { id: 'cherry', name: 'Cherry (Premium)', lang: 'en-US' },
        { id: 'sophia', name: 'Sophia (Premium)', lang: 'en-US' },
        { id: 'karen', name: 'Karen (Premium)', lang: 'en-US' },
      ];

      const allVoices = [...customVoices, ...englishVoices];
      setVoices(allVoices);
      setAvailableVoices(allVoices.map(v => v.name));

      // Set default voice
      if (!selectedVoice && allVoices.length > 0) {
        setSelectedVoice(allVoices[0].id);
      }
    };

    // Chrome loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
    
    // Initial load
    loadVoices();
  }, [setAvailableVoices, setSelectedVoice, selectedVoice]);

  // Get text to synthesize from search results
  const getTextToSpeak = useCallback(() => {
    if (searchResults.length === 0) return '';
    
    // Combine all text results
    return searchResults
      .filter(result => result.type === 'text')
      .map(result => result.content)
      .join('. ');
  }, [searchResults]);

  const handlePlay = useCallback(async () => {
    const text = getTextToSpeak();
    if (!text) return;

    const voice = voices.find(v => v.id === selectedVoice);
    if (!voice) return;

    // Check if it's a custom voice (use API)
    if (['cherry', 'sophia', 'karen'].includes(voice.id)) {
      try {
        // Use the orchestrator service to get synthesized audio
        const audioBlob = await orchestratorService.synthesizeSpeech(text, {
          voice: voice.id,
          rate,
          pitch,
          volume,
        });

        // Create audio element and play
        const audioUrl = URL.createObjectURL(audioBlob);
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.volume = volume;
          audioRef.current.playbackRate = rate;
          await audioRef.current.play();
          setIsPlaying(true);
        }
      } catch (error) {
        console.error('Failed to synthesize speech:', error);
      }
    } else {
      // Use browser's speech synthesis
      if (utteranceRef.current) {
        window.speechSynthesis.cancel();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = window.speechSynthesis.getVoices().find(
        v => v.voiceURI === voice.id
      ) || null;
      utterance.volume = volume;
      utterance.rate = rate;
      utterance.pitch = pitch;

      utterance.onstart = () => {
        setIsPlaying(true);
        setIsPaused(false);
      };

      utterance.onend = () => {
        setIsPlaying(false);
        setIsPaused(false);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsPlaying(false);
        setIsPaused(false);
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    }
  }, [getTextToSpeak, selectedVoice, voices, volume, rate, pitch]);

  const handlePause = useCallback(() => {
    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      setIsPaused(true);
    } else if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  }, []);

  const handleResume = useCallback(() => {
    if (audioRef.current && audioRef.current.paused) {
      audioRef.current.play();
      setIsPaused(false);
    } else if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  }, []);

  const handleStop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  }, []);

  const handleDownload = useCallback(async () => {
    const text = getTextToSpeak();
    if (!text) return;

    const voice = voices.find(v => v.id === selectedVoice);
    if (!voice) return;

    try {
      const audioBlob = await orchestratorService.synthesizeSpeech(text, {
        voice: voice.id,
        rate,
        pitch,
        volume,
      });

      // Create download link
      const url = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `speech-${Date.now()}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download speech:', error);
    }
  }, [getTextToSpeak, selectedVoice, voices, rate, pitch, volume]);

  if (!isSupported) {
    return (
      <Card className="p-4 bg-red-900/20 border-red-800">
        <p className="text-sm text-red-400">
          Text-to-speech is not supported in this browser.
        </p>
      </Card>
    );
  }

  const hasText = getTextToSpeak().length > 0;

  return (
    <div className="space-y-4">
      {/* Voice Selection */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-400">Voice</label>
        <Select value={selectedVoice} onValueChange={setSelectedVoice}>
          <SelectTrigger className="w-full bg-gray-800 border-gray-700">
            <SelectValue placeholder="Select a voice" />
          </SelectTrigger>
          <SelectContent>
            {voices.map(voice => (
              <SelectItem key={voice.id} value={voice.id}>
                {voice.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Voice Controls */}
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-gray-400">Volume</label>
            <span className="text-sm text-gray-500">{Math.round(volume * 100)}%</span>
          </div>
          <Slider
            value={[volume]}
            onValueChange={([v]) => setVolume(v)}
            min={0}
            max={1}
            step={0.1}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-gray-400">Speed</label>
            <span className="text-sm text-gray-500">{rate}x</span>
          </div>
          <Slider
            value={[rate]}
            onValueChange={([v]) => setRate(v)}
            min={0.5}
            max={2}
            step={0.1}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm font-medium text-gray-400">Pitch</label>
            <span className="text-sm text-gray-500">{pitch}</span>
          </div>
          <Slider
            value={[pitch]}
            onValueChange={([v]) => setPitch(v)}
            min={0.5}
            max={2}
            step={0.1}
            className="w-full"
          />
        </div>
      </div>

      {/* Playback Controls */}
      <div className="flex items-center justify-center gap-2">
        {!isPlaying ? (
          <Button
            onClick={handlePlay}
            disabled={!hasText}
            className="gap-2"
            variant="default"
          >
            <Play className="w-4 h-4" />
            Play
          </Button>
        ) : (
          <>
            {isPaused ? (
              <Button
                onClick={handleResume}
                className="gap-2"
                variant="default"
              >
                <Play className="w-4 h-4" />
                Resume
              </Button>
            ) : (
              <Button
                onClick={handlePause}
                className="gap-2"
                variant="default"
              >
                <Pause className="w-4 h-4" />
                Pause
              </Button>
            )}
            <Button
              onClick={handleStop}
              variant="outline"
              className="gap-2"
            >
              <VolumeX className="w-4 h-4" />
              Stop
            </Button>
          </>
        )}
        
        <Button
          onClick={handleDownload}
          disabled={!hasText}
          variant="outline"
          className="gap-2"
        >
          <Download className="w-4 h-4" />
          Download
        </Button>
      </div>

      {/* Hidden audio element for custom voices */}
      <audio
        ref={audioRef}
        onEnded={() => {
          setIsPlaying(false);
          setIsPaused(false);
        }}
        className="hidden"
      />

      {!hasText && (
        <p className="text-xs text-gray-500 text-center">
          Perform a search to generate speech from the results
        </p>
      )}
    </div>
  );
};