#!/bin/bash

echo "📱 ORCHESTRA AI PRIVATE MOBILE APP SETUP"
echo "========================================"

# Check if we're in the right directory
if [ ! -d "mobile-app" ]; then
    echo "Creating mobile-app directory..."
    mkdir -p mobile-app
fi

cd mobile-app

echo "📋 Step 1: Installing global dependencies..."
echo "Installing Expo CLI and EAS CLI..."
npm install -g @expo/cli eas-cli

echo "📋 Step 2: Creating Expo project structure..."

# Create package.json for React Native with Expo
cat > package.json << 'EOF'
{
  "name": "orchestra-ai-mobile",
  "version": "1.0.0",
  "main": "node_modules/expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "build:android": "eas build --platform android",
    "build:ios": "eas build --platform ios",
    "build:both": "eas build --platform all"
  },
  "dependencies": {
    "expo": "~49.0.0",
    "expo-dev-client": "~2.4.0",
    "react": "18.2.0",
    "react-native": "0.72.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/stack": "^6.3.0",
    "react-native-screens": "~3.22.0",
    "react-native-safe-area-context": "4.6.3",
    "expo-status-bar": "~1.6.0",
    "expo-speech": "~11.3.0",
    "expo-av": "~13.4.0",
    "expo-camera": "~13.4.0",
    "expo-local-authentication": "~13.4.0",
    "expo-secure-store": "~12.3.0",
    "expo-notifications": "~0.20.0",
    "@react-native-async-storage/async-storage": "1.18.2"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "@types/react": "~18.2.14",
    "@types/react-native": "~0.72.2",
    "typescript": "^5.1.3"
  },
  "private": true
}
EOF

echo "📋 Step 3: Creating app configuration..."

# Create app.json
cat > app.json << 'EOF'
{
  "expo": {
    "name": "Orchestra AI",
    "slug": "orchestra-ai-private",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1a1a1a"
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.cherry-ai.orchestra-private",
      "buildNumber": "1",
      "infoPlist": {
        "NSCameraUsageDescription": "Orchestra AI uses camera for document scanning and visual input",
        "NSMicrophoneUsageDescription": "Orchestra AI uses microphone for voice commands and audio input",
        "NSFaceIDUsageDescription": "Orchestra AI uses Face ID for secure authentication"
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#1a1a1a"
      },
      "package": "com.cherryai.orchestra.private",
      "versionCode": 1,
      "permissions": [
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.USE_FINGERPRINT",
        "android.permission.USE_BIOMETRIC"
      ]
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "plugins": [
      "expo-dev-client",
      [
        "expo-local-authentication",
        {
          "faceIDPermission": "Allow Orchestra AI to use Face ID for secure authentication"
        }
      ]
    ],
    "extra": {
      "eas": {
        "projectId": "orchestra-ai-private"
      }
    }
  }
}
EOF

echo "📋 Step 4: Creating EAS build configuration..."

# Create eas.json
cat > eas.json << 'EOF'
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "resourceClass": "m-medium"
      },
      "android": {
        "buildType": "apk",
        "gradleCommand": ":app:assembleDebug"
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "resourceClass": "m-medium"
      },
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "ios": {
        "resourceClass": "m-medium"
      },
      "android": {
        "buildType": "aab"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
EOF

echo "📋 Step 5: Creating TypeScript configuration..."

# Create tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/screens/*": ["src/screens/*"],
      "@/services/*": ["src/services/*"],
      "@/utils/*": ["src/utils/*"]
    }
  }
}
EOF

echo "📋 Step 6: Creating source code structure..."

# Create directories
mkdir -p src/{components,screens,services,utils,types}
mkdir -p assets

echo "📋 Step 7: Creating main App component..."

# Create App.tsx
cat > App.tsx << 'EOF'
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, SafeAreaView } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import ChatScreen from './src/screens/ChatScreen';
import DashboardScreen from './src/screens/DashboardScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <NavigationContainer>
        <Stack.Navigator 
          initialRouteName="Dashboard"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#1a1a1a',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen 
            name="Dashboard" 
            component={DashboardScreen} 
            options={{ title: 'Orchestra AI' }}
          />
          <Stack.Screen 
            name="Chat" 
            component={ChatScreen} 
            options={{ title: 'AI Chat' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
      <StatusBar style="light" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
});
EOF

echo "📋 Step 8: Creating screen components..."

# Create DashboardScreen
cat > src/screens/DashboardScreen.tsx << 'EOF'
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';

export default function DashboardScreen() {
  const navigation = useNavigation();

  const features = [
    { title: 'AI Chat', description: 'Chat with Orchestra AI', screen: 'Chat' },
    { title: 'Voice Commands', description: 'Voice-powered interactions' },
    { title: 'Project Management', description: 'Linear, GitHub, Asana integration' },
    { title: 'Knowledge Base', description: 'Notion integration and search' },
    { title: 'Analytics', description: 'Performance metrics and insights' },
    { title: 'Settings', description: 'App configuration and preferences' },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Orchestra AI</Text>
        <Text style={styles.subtitle}>Your Personal AI Assistant</Text>
      </View>
      
      <View style={styles.featuresContainer}>
        {features.map((feature, index) => (
          <TouchableOpacity
            key={index}
            style={styles.featureCard}
            onPress={() => feature.screen && navigation.navigate(feature.screen as never)}
          >
            <Text style={styles.featureTitle}>{feature.title}</Text>
            <Text style={styles.featureDescription}>{feature.description}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
  },
  featuresContainer: {
    padding: 20,
  },
  featureCard: {
    backgroundColor: '#2a2a2a',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  featureDescription: {
    fontSize: 14,
    color: '#888',
  },
});
EOF

# Create ChatScreen
cat > src/screens/ChatScreen.tsx << 'EOF'
import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  TouchableOpacity, 
  ScrollView,
  KeyboardAvoidingView,
  Platform 
} from 'react-native';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m Orchestra AI. How can I help you today?',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');

  const sendMessage = () => {
    if (inputText.trim()) {
      const newMessage: Message = {
        id: Date.now().toString(),
        text: inputText,
        isUser: true,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, newMessage]);
      setInputText('');

      // Simulate AI response
      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: 'I understand your request. In the full version, I would process this through the Orchestra AI backend with access to Linear, GitHub, Asana, and Notion integrations.',
          isUser: false,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      }, 1000);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.messagesContainer}>
        {messages.map((message) => (
          <View
            key={message.id}
            style={[
              styles.messageContainer,
              message.isUser ? styles.userMessage : styles.aiMessage,
            ]}
          >
            <Text style={styles.messageText}>{message.text}</Text>
            <Text style={styles.timestamp}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </View>
        ))}
      </ScrollView>
      
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type your message..."
          placeholderTextColor="#888"
          multiline
        />
        <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  messageContainer: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 12,
    maxWidth: '80%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  aiMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#2a2a2a',
  },
  messageText: {
    color: '#fff',
    fontSize: 16,
  },
  timestamp: {
    color: '#888',
    fontSize: 12,
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#2a2a2a',
    color: '#fff',
    padding: 12,
    borderRadius: 8,
    marginRight: 8,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: 'center',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
EOF

echo "📋 Step 9: Installing dependencies..."
npm install

echo "📋 Step 10: Creating placeholder assets..."

# Create a simple icon (you can replace with actual icons later)
mkdir -p assets
echo "Add your app icons to the assets/ directory:" > assets/README.md
echo "- icon.png (1024x1024)" >> assets/README.md
echo "- adaptive-icon.png (1024x1024)" >> assets/README.md
echo "- splash.png (1284x2778)" >> assets/README.md
echo "- favicon.png (48x48)" >> assets/README.md

echo "✅ Mobile app setup complete!"
echo ""
echo "📱 NEXT STEPS:"
echo ""
echo "🍎 FOR iOS (Requires Apple Developer Account):"
echo "1. Sign up for Apple Developer Program (\$99/year)"
echo "2. Run: eas login"
echo "3. Run: eas build:configure"
echo "4. Run: eas build --platform ios --profile development"
echo "5. Install the app from the provided TestFlight link"
echo "6. Run: npx expo start --dev-client"
echo "7. Scan QR code with your iPhone"
echo ""
echo "🤖 FOR ANDROID (Free):"
echo "1. Enable Developer Options on your Android phone"
echo "2. Enable USB Debugging and Install Unknown Apps"
echo "3. Run: eas login"
echo "4. Run: eas build:configure"
echo "5. Run: eas build --platform android --profile development"
echo "6. Download and install the APK on your phone"
echo "7. Run: npx expo start --dev-client"
echo "8. Scan QR code with your Android phone"
echo ""
echo "🎯 DEVELOPMENT WORKFLOW:"
echo "- Make code changes in src/"
echo "- Run: npx expo start --dev-client"
echo "- Scan QR code to see changes instantly"
echo "- No need to rebuild unless you change native dependencies"
echo ""
echo "🎉 Your private Orchestra AI mobile apps are ready for development!"

