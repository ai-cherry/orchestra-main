import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { VoiceRecognitionService } from '../../services/voiceRecognition';

export const VoiceInput = ({ persona, onCommand, className = "" }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [voiceService] = useState(() => new VoiceRecognitionService());
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    setIsSupported(VoiceRecognitionService.isSupported());
  }, []);

  const callMcpTool = async (toolName, arguments) => {
    try {
      // This would be replaced with actual MCP service call
      // For now, simulate the response
      const response = await fetch('/api/mcp/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool: toolName,
          arguments: arguments
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.text();
      return result;
    } catch (error) {
      console.error('MCP call failed:', error);
      // Return a mock response for demonstration
      return `Processed voice command: "${arguments.transcript}" for ${arguments.persona}`;
    }
  };

  const handleVoiceStart = async () => {
    if (!isSupported) {
      setError('Voice recognition not supported in this browser');
      return;
    }

    setError(null);
    setTranscript('');

    const success = await voiceService.startListening(
      async (finalTranscript) => {
        setTranscript(finalTranscript);
        
        try {
          const result = await callMcpTool('process_voice_command', {
            transcript: finalTranscript,
            persona: persona,
            context: { 
              currentPath: window.location.pathname,
              timestamp: new Date().toISOString()
            },
            confidence: 0.8 // Mock confidence score
          });
          
          if (onCommand) {
            onCommand({
              type: 'voice_command',
              transcript: finalTranscript,
              result: result,
              persona: persona
            });
          }
        } catch (error) {
          setError('Failed to process voice command');
          console.error('Voice command processing error:', error);
        }
      },
      (error) => {
        setError(`Voice recognition error: ${error}`);
        setIsListening(false);
      },
      () => {
        setIsListening(false);
      }
    );

    if (success) {
      setIsListening(true);
    }
  };

  const handleVoiceStop = () => {
    voiceService.stop();
    setIsListening(false);
  };

  if (!isSupported) {
    return (
      <div className={`voice-input-unsupported ${className}`}>
        <div className="unsupported-message">
          🎤 Voice recognition not supported in this browser
        </div>
      </div>
    );
  }

  return (
    <div className={`voice-input ${className}`}>
      <motion.button
        className={`voice-button ${persona} ${isListening ? 'listening' : ''}`}
        onClick={isListening ? handleVoiceStop : handleVoiceStart}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={isListening ? { 
          boxShadow: [
            "0 0 0 0 rgba(255, 0, 0, 0.7)", 
            "0 0 0 10px rgba(255, 0, 0, 0)"
          ],
          transition: { duration: 1, repeat: Infinity }
        } : {}}
        disabled={!isSupported}
      >
        <span className="voice-icon">
          {isListening ? '🔴' : '🎤'}
        </span>
        <span className="voice-text">
          {isListening ? 'Listening...' : 'Voice Input'}
        </span>
      </motion.button>

      {transcript && (
        <motion.div 
          className="transcript"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
        >
          <div className="transcript-label">You said:</div>
          <div className="transcript-text">"{transcript}"</div>
        </motion.div>
      )}

      {error && (
        <motion.div 
          className="voice-error"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </motion.div>
      )}

      <style jsx>{`
        .voice-input {
          display: flex;
          flex-direction: column;
          gap: 12px;
          align-items: center;
        }

        .voice-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          border: none;
          border-radius: 25px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .voice-button.cherry {
          background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }

        .voice-button.sophia {
          background: linear-gradient(135deg, #4834d4 0%, #686de0 100%);
        }

        .voice-button.karen {
          background: linear-gradient(135deg, #00d2d3 0%, #54a0ff 100%);
        }

        .voice-button.listening {
          animation: pulse 1s infinite;
        }

        .voice-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .voice-icon {
          font-size: 18px;
        }

        .transcript {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 12px;
          padding: 16px;
          max-width: 300px;
          text-align: center;
        }

        .transcript-label {
          font-size: 12px;
          opacity: 0.7;
          margin-bottom: 8px;
        }

        .transcript-text {
          font-style: italic;
          font-weight: 500;
        }

        .voice-error {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(255, 0, 0, 0.1);
          color: #ff4757;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 14px;
        }

        .voice-input-unsupported {
          padding: 16px;
          text-align: center;
          opacity: 0.6;
        }

        @keyframes pulse {
          0% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.05);
          }
          100% {
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}; 