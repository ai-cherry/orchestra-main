import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Animated,
  Vibration,
} from 'react-native';
import * as Speech from 'expo-speech';
import { Audio } from 'expo-av';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  type?: 'text' | 'voice' | 'action';
}

interface AIPersona {
  id: string;
  name: string;
  color: string;
  description: string;
  avatar: string;
}

export default function EnhancedChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m Orchestra AI. I can help you with Linear tasks, GitHub projects, Asana coordination, Notion documents, and much more. How can I assist you today?',
      isUser: false,
      timestamp: new Date(),
      type: 'text',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<AIPersona>({
    id: 'sophia',
    name: 'Sophia',
    color: '#007AFF',
    description: 'Business Intelligence',
    avatar: '💼',
  });

  const scrollViewRef = useRef<ScrollView>(null);
  const recordingAnimation = useRef(new Animated.Value(0)).current;
  const typingAnimation = useRef(new Animated.Value(0)).current;

  const personas: AIPersona[] = [
    {
      id: 'sophia',
      name: 'Sophia',
      color: '#007AFF',
      description: 'Business Intelligence',
      avatar: '💼',
    },
    {
      id: 'karen',
      name: 'Karen',
      color: '#34C759',
      description: 'Clinical Research',
      avatar: '🔬',
    },
    {
      id: 'cherry',
      name: 'Cherry',
      color: '#FF9500',
      description: 'Creative Assistant',
      avatar: '🌟',
    },
    {
      id: 'master',
      name: 'Master',
      color: '#FF3B30',
      description: 'Advanced Operations',
      avatar: '⚡',
    },
  ];

  useEffect(() => {
    if (isTyping) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(typingAnimation, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(typingAnimation, {
            toValue: 0,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      typingAnimation.setValue(0);
    }
  }, [isTyping]);

  useEffect(() => {
    if (isRecording) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(recordingAnimation, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(recordingAnimation, {
            toValue: 0,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      recordingAnimation.setValue(0);
    }
  }, [isRecording]);

  const sendMessage = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date(),
      type: text ? 'voice' : 'text',
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');
    setIsTyping(true);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Simulate AI processing
    try {
      const response = await processAIRequest(messageText);
      
      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: response,
          isUser: false,
          timestamp: new Date(),
          type: 'text',
        };
        
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
        
        // Text-to-speech for AI responses
        Speech.speak(response, {
          language: 'en-US',
          pitch: 1.0,
          rate: 0.9,
        });

        setTimeout(() => {
          scrollViewRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }, 1500 + Math.random() * 1000); // Simulate processing time
    } catch (error) {
      setIsTyping(false);
      Alert.alert('Error', 'Failed to process your request. Please try again.');
    }
  };

  const processAIRequest = async (message: string): Promise<string> => {
    // Simulate AI processing with context-aware responses
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('linear') || lowerMessage.includes('task') || lowerMessage.includes('issue')) {
      return `I can help you with Linear tasks! Based on your current projects, you have 5 active issues. Would you like me to:\n\n• Create a new issue\n• Update existing tasks\n• Show project progress\n• Sync with your team`;
    }
    
    if (lowerMessage.includes('github') || lowerMessage.includes('repository') || lowerMessage.includes('code')) {
      return `GitHub integration is ready! I can help you:\n\n• Review pull requests\n• Check repository status\n• Create new branches\n• Analyze code metrics\n\nWhich repository would you like to work with?`;
    }
    
    if (lowerMessage.includes('asana') || lowerMessage.includes('project')) {
      return `Asana project management at your service! I can:\n\n• Create new tasks\n• Update project timelines\n• Assign team members\n• Generate progress reports\n\nWhat project needs attention?`;
    }
    
    if (lowerMessage.includes('notion') || lowerMessage.includes('document') || lowerMessage.includes('note')) {
      return `Notion integration is active! I can help you:\n\n• Create new pages\n• Search existing documents\n• Update knowledge base\n• Organize information\n\nWhat would you like to document?`;
    }
    
    if (lowerMessage.includes('voice') || lowerMessage.includes('speak') || lowerMessage.includes('listen')) {
      return `Voice commands are fully functional! You can:\n\n• Speak naturally to give commands\n• Ask me to read responses aloud\n• Use voice for hands-free operation\n• Record voice notes for later\n\nTry saying "Create a new Linear task" or "Show my GitHub repositories"`;
    }
    
    // Default intelligent response
    return `I understand you're asking about "${message}". As Orchestra AI, I can help you with:\n\n• Linear task management\n• GitHub repository operations\n• Asana project coordination\n• Notion document management\n• Voice-powered interactions\n• Cross-platform analytics\n\nWhat specific action would you like me to take?`;
  };

  const startVoiceRecording = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Please grant microphone permission to use voice features.');
        return;
      }

      setIsRecording(true);
      Vibration.vibrate(50); // Haptic feedback
      
      // Simulate voice recording (in production, implement actual speech-to-text)
      setTimeout(() => {
        setIsRecording(false);
        const voiceCommands = [
          'Create a new Linear task for mobile app testing',
          'Show me my GitHub repositories',
          'What are my Asana deadlines this week?',
          'Search Notion for project documentation',
          'Give me a summary of today\'s activities',
        ];
        
        const randomCommand = voiceCommands[Math.floor(Math.random() * voiceCommands.length)];
        sendMessage(randomCommand);
      }, 2000 + Math.random() * 2000);
      
    } catch (error) {
      setIsRecording(false);
      Alert.alert('Error', 'Failed to start voice recording. Please try again.');
    }
  };

  const switchPersona = (persona: AIPersona) => {
    setSelectedPersona(persona);
    const switchMessage: Message = {
      id: Date.now().toString(),
      text: `Switched to ${persona.name} - ${persona.description}. How can I help you with ${persona.name.toLowerCase()}-specific tasks?`,
      isUser: false,
      timestamp: new Date(),
      type: 'action',
    };
    setMessages(prev => [...prev, switchMessage]);
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Persona Selector */}
      <View style={styles.personaContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {personas.map((persona) => (
            <TouchableOpacity
              key={persona.id}
              style={[
                styles.personaButton,
                { backgroundColor: persona.color },
                selectedPersona.id === persona.id && styles.selectedPersona,
              ]}
              onPress={() => switchPersona(persona)}
            >
              <Text style={styles.personaAvatar}>{persona.avatar}</Text>
              <Text style={styles.personaName}>{persona.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Messages */}
      <ScrollView 
        ref={scrollViewRef}
        style={styles.messagesContainer}
        showsVerticalScrollIndicator={false}
      >
        {messages.map((message) => (
          <View
            key={message.id}
            style={[
              styles.messageContainer,
              message.isUser ? styles.userMessage : styles.aiMessage,
            ]}
          >
            {!message.isUser && (
              <View style={[styles.avatarContainer, { backgroundColor: selectedPersona.color }]}>
                <Text style={styles.avatarText}>{selectedPersona.avatar}</Text>
              </View>
            )}
            
            <View style={[
              styles.messageBubble,
              message.isUser ? styles.userBubble : styles.aiBubble,
              message.type === 'voice' && styles.voiceMessage,
              message.type === 'action' && styles.actionMessage,
            ]}>
              {message.type === 'voice' && (
                <Text style={styles.voiceIndicator}>🎤 Voice Message</Text>
              )}
              {message.type === 'action' && (
                <Text style={styles.actionIndicator}>⚡ System Action</Text>
              )}
              <Text style={[
                styles.messageText,
                message.isUser ? styles.userText : styles.aiText,
              ]}>
                {message.text}
              </Text>
              <Text style={styles.timestamp}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
            </View>
          </View>
        ))}
        
        {/* Typing Indicator */}
        {isTyping && (
          <View style={[styles.messageContainer, styles.aiMessage]}>
            <View style={[styles.avatarContainer, { backgroundColor: selectedPersona.color }]}>
              <Text style={styles.avatarText}>{selectedPersona.avatar}</Text>
            </View>
            <View style={[styles.messageBubble, styles.aiBubble]}>
              <Animated.View style={[styles.typingIndicator, {
                opacity: typingAnimation,
              }]}>
                <Text style={styles.typingText}>● ● ●</Text>
              </Animated.View>
            </View>
          </View>
        )}
      </ScrollView>
      
      {/* Input Container */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type your message..."
          placeholderTextColor="#8E8E93"
          multiline
          maxLength={1000}
        />
        
        <TouchableOpacity
          style={[styles.voiceButton, isRecording && styles.recordingButton]}
          onPress={startVoiceRecording}
          disabled={isRecording}
        >
          <Animated.View style={{
            transform: [{
              scale: recordingAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: [1, 1.2],
              }),
            }],
          }}>
            <Text style={styles.voiceButtonText}>
              {isRecording ? '🔴' : '🎤'}
            </Text>
          </Animated.View>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.sendButton, !inputText.trim() && styles.disabledButton]} 
          onPress={() => sendMessage()}
          disabled={!inputText.trim()}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  personaContainer: {
    backgroundColor: '#1C1C1E',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  personaButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 12,
    alignItems: 'center',
    minWidth: 80,
  },
  selectedPersona: {
    transform: [{ scale: 1.1 }],
  },
  personaAvatar: {
    fontSize: 16,
    marginBottom: 2,
  },
  personaName: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  messageContainer: {
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  aiMessage: {
    justifyContent: 'flex-start',
  },
  avatarContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  avatarText: {
    fontSize: 16,
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: '#1C1C1E',
    borderBottomLeftRadius: 4,
  },
  voiceMessage: {
    borderWidth: 2,
    borderColor: '#34C759',
  },
  actionMessage: {
    borderWidth: 2,
    borderColor: '#FF9500',
  },
  voiceIndicator: {
    color: '#34C759',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  actionIndicator: {
    color: '#FF9500',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  userText: {
    color: '#FFFFFF',
  },
  aiText: {
    color: '#FFFFFF',
  },
  timestamp: {
    color: '#8E8E93',
    fontSize: 12,
    marginTop: 4,
  },
  typingIndicator: {
    paddingVertical: 8,
  },
  typingText: {
    color: '#8E8E93',
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#1C1C1E',
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#2C2C2E',
    color: '#FFFFFF',
    padding: 12,
    borderRadius: 20,
    marginRight: 8,
    maxHeight: 100,
    fontSize: 16,
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#34C759',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  recordingButton: {
    backgroundColor: '#FF3B30',
  },
  voiceButtonText: {
    fontSize: 20,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    justifyContent: 'center',
  },
  disabledButton: {
    backgroundColor: '#2C2C2E',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 16,
  },
});

