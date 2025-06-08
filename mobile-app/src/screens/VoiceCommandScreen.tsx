import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Animated,
  Vibration,
} from 'react-native';
import * as Speech from 'expo-speech';
import { Audio } from 'expo-av';

interface VoiceCommand {
  id: string;
  command: string;
  description: string;
  category: 'linear' | 'github' | 'asana' | 'notion' | 'general';
  example: string;
}

export default function VoiceCommandScreen() {
  const [isListening, setIsListening] = useState(false);
  const [lastCommand, setLastCommand] = useState<string>('');
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [pulseAnimation] = useState(new Animated.Value(1));

  const voiceCommands: VoiceCommand[] = [
    {
      id: '1',
      command: 'Create Linear task',
      description: 'Create a new Linear issue',
      category: 'linear',
      example: 'Create a Linear task for mobile app testing',
    },
    {
      id: '2',
      command: 'Show GitHub repos',
      description: 'Display GitHub repositories',
      category: 'github',
      example: 'Show me my GitHub repositories',
    },
    {
      id: '3',
      command: 'List Asana tasks',
      description: 'Show Asana project tasks',
      category: 'asana',
      example: 'List my Asana tasks for this week',
    },
    {
      id: '4',
      command: 'Search Notion',
      description: 'Search Notion documents',
      category: 'notion',
      example: 'Search Notion for project documentation',
    },
    {
      id: '5',
      command: 'Daily summary',
      description: 'Get daily activity summary',
      category: 'general',
      example: 'Give me a summary of today\'s activities',
    },
    {
      id: '6',
      command: 'Start timer',
      description: 'Start a work timer',
      category: 'general',
      example: 'Start a 25-minute focus timer',
    },
    {
      id: '7',
      command: 'Schedule meeting',
      description: 'Schedule a new meeting',
      category: 'general',
      example: 'Schedule a meeting for tomorrow at 2 PM',
    },
    {
      id: '8',
      command: 'Check deadlines',
      description: 'Show upcoming deadlines',
      category: 'general',
      example: 'What are my deadlines this week?',
    },
  ];

  useEffect(() => {
    if (isListening) {
      startPulseAnimation();
    } else {
      stopPulseAnimation();
    }
  }, [isListening]);

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnimation, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnimation, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopPulseAnimation = () => {
    pulseAnimation.setValue(1);
  };

  const startListening = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          'Permission Required',
          'Please grant microphone permission to use voice commands.'
        );
        return;
      }

      setIsListening(true);
      Vibration.vibrate(50);

      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Start recording
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(newRecording);

      // Simulate voice recognition (in production, use actual speech-to-text)
      setTimeout(() => {
        stopListening();
        const sampleCommands = [
          'Create a Linear task for mobile app testing',
          'Show me my GitHub repositories',
          'List my Asana tasks for this week',
          'Search Notion for project documentation',
          'Give me a summary of today\'s activities',
          'Start a 25-minute focus timer',
        ];
        const randomCommand = sampleCommands[Math.floor(Math.random() * sampleCommands.length)];
        processVoiceCommand(randomCommand);
      }, 3000);

    } catch (error) {
      console.error('Error starting voice recording:', error);
      setIsListening(false);
      Alert.alert('Error', 'Failed to start voice recording. Please try again.');
    }
  };

  const stopListening = async () => {
    try {
      if (recording) {
        await recording.stopAndUnloadAsync();
        setRecording(null);
      }
      setIsListening(false);
      Vibration.vibrate(100);
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  const processVoiceCommand = (command: string) => {
    setLastCommand(command);
    
    // Provide voice feedback
    Speech.speak(`Processing command: ${command}`, {
      language: 'en-US',
      pitch: 1.0,
      rate: 0.9,
    });

    // Simulate command processing
    setTimeout(() => {
      let response = '';
      const lowerCommand = command.toLowerCase();

      if (lowerCommand.includes('linear') || lowerCommand.includes('task')) {
        response = 'Linear task created successfully. Issue ORG-127 has been added to your backlog.';
      } else if (lowerCommand.includes('github') || lowerCommand.includes('repo')) {
        response = 'Showing your GitHub repositories. You have 5 active repositories with 3 pending pull requests.';
      } else if (lowerCommand.includes('asana')) {
        response = 'You have 8 Asana tasks this week. 3 are due tomorrow and 2 are overdue.';
      } else if (lowerCommand.includes('notion') || lowerCommand.includes('search')) {
        response = 'Found 12 Notion documents matching your search. Opening the most relevant results.';
      } else if (lowerCommand.includes('summary') || lowerCommand.includes('today')) {
        response = 'Today you completed 5 tasks, created 2 new issues, and had 3 meetings. Great productivity!';
      } else if (lowerCommand.includes('timer')) {
        response = 'Starting a 25-minute focus timer. I\'ll notify you when it\'s time for a break.';
      } else {
        response = 'Command processed. Check the main dashboard for updates.';
      }

      Speech.speak(response, {
        language: 'en-US',
        pitch: 1.0,
        rate: 0.9,
      });

      Alert.alert('Voice Command Processed', response);
    }, 1500);
  };

  const getCategoryColor = (category: VoiceCommand['category']) => {
    switch (category) {
      case 'linear': return '#5856D6';
      case 'github': return '#FF9500';
      case 'asana': return '#FF3B30';
      case 'notion': return '#000000';
      case 'general': return '#007AFF';
      default: return '#8E8E93';
    }
  };

  const getCategoryIcon = (category: VoiceCommand['category']) => {
    switch (category) {
      case 'linear': return '📋';
      case 'github': return '🐙';
      case 'asana': return '✅';
      case 'notion': return '📝';
      case 'general': return '⚡';
      default: return '🔧';
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Voice Commands</Text>
        <Text style={styles.subtitle}>Speak naturally to control Orchestra AI</Text>
      </View>

      {/* Voice Input */}
      <View style={styles.voiceInputContainer}>
        <TouchableOpacity
          style={[styles.voiceButton, isListening && styles.listeningButton]}
          onPress={isListening ? stopListening : startListening}
        >
          <Animated.View
            style={[
              styles.voiceButtonInner,
              {
                transform: [{ scale: pulseAnimation }],
              },
            ]}
          >
            <Text style={styles.voiceButtonText}>
              {isListening ? '🔴' : '🎤'}
            </Text>
          </Animated.View>
        </TouchableOpacity>
        
        <Text style={styles.voiceStatus}>
          {isListening ? 'Listening...' : 'Tap to speak'}
        </Text>
        
        {lastCommand && (
          <View style={styles.lastCommandContainer}>
            <Text style={styles.lastCommandLabel}>Last Command:</Text>
            <Text style={styles.lastCommandText}>{lastCommand}</Text>
          </View>
        )}
      </View>

      {/* Available Commands */}
      <View style={styles.commandsSection}>
        <Text style={styles.sectionTitle}>Available Commands</Text>
        <ScrollView style={styles.commandsList} showsVerticalScrollIndicator={false}>
          {voiceCommands.map((command) => (
            <TouchableOpacity
              key={command.id}
              style={styles.commandCard}
              onPress={() => processVoiceCommand(command.example)}
            >
              <View style={styles.commandHeader}>
                <View style={styles.commandIcon}>
                  <Text style={styles.commandIconText}>
                    {getCategoryIcon(command.category)}
                  </Text>
                </View>
                <View style={styles.commandInfo}>
                  <Text style={styles.commandTitle}>{command.command}</Text>
                  <Text style={styles.commandDescription}>{command.description}</Text>
                </View>
                <View
                  style={[
                    styles.categoryBadge,
                    { backgroundColor: getCategoryColor(command.category) },
                  ]}
                >
                  <Text style={styles.categoryText}>{command.category}</Text>
                </View>
              </View>
              <Text style={styles.commandExample}>
                Example: "{command.example}"
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Tips */}
      <View style={styles.tipsContainer}>
        <Text style={styles.tipsTitle}>💡 Voice Tips</Text>
        <Text style={styles.tipsText}>
          • Speak clearly and naturally{'\n'}
          • Use specific keywords like "Linear", "GitHub", "Asana"{'\n'}
          • Wait for the beep before speaking{'\n'}
          • Commands work offline after initial setup
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    padding: 20,
    paddingTop: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
  },
  voiceInputContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  voiceButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  listeningButton: {
    backgroundColor: '#FF3B30',
  },
  voiceButtonInner: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButtonText: {
    fontSize: 40,
  },
  voiceStatus: {
    fontSize: 18,
    color: '#FFFFFF',
    fontWeight: '600',
    marginBottom: 16,
  },
  lastCommandContainer: {
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 20,
    alignItems: 'center',
  },
  lastCommandLabel: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  lastCommandText: {
    fontSize: 16,
    color: '#FFFFFF',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  commandsSection: {
    flex: 1,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  commandsList: {
    flex: 1,
  },
  commandCard: {
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  commandHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  commandIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2C2C2E',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  commandIconText: {
    fontSize: 20,
  },
  commandInfo: {
    flex: 1,
  },
  commandTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  commandDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  commandExample: {
    fontSize: 14,
    color: '#007AFF',
    fontStyle: 'italic',
  },
  tipsContainer: {
    backgroundColor: '#1C1C1E',
    margin: 20,
    padding: 16,
    borderRadius: 12,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  tipsText: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
});

