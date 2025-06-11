import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

// Import screens
import EnhancedDashboardScreen from './src/screens/EnhancedDashboardScreen';
import EnhancedChatScreen from './src/screens/EnhancedChatScreen';
import LinearIntegrationScreen from './src/screens/LinearIntegrationScreen';
import VoiceCommandScreen from './src/screens/VoiceCommandScreen';
import SettingsScreen from './src/screens/SettingsScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: '#1C1C1E',
          borderTopColor: '#2C2C2E',
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        headerStyle: {
          backgroundColor: '#1C1C1E',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Tab.Screen 
        name="Dashboard" 
        component={EnhancedDashboardScreen}
        options={{
          title: 'Orchestra AI',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>🏠</Text>,
          headerShown: false,
        }}
      />
      <Tab.Screen 
        name="Chat" 
        component={EnhancedChatScreen}
        options={{
          title: 'AI Chat',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>💬</Text>,
        }}
      />
      <Tab.Screen 
        name="Linear" 
        component={LinearIntegrationScreen}
        options={{
          title: 'Linear',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>📋</Text>,
          headerShown: false,
        }}
      />
      <Tab.Screen 
        name="Voice" 
        component={VoiceCommandScreen}
        options={{
          title: 'Voice',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>🎤</Text>,
        }}
      />
      <Tab.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{
          title: 'Settings',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>⚙️</Text>,
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Main" component={TabNavigator} />
        </Stack.Navigator>
      </NavigationContainer>
      <StatusBar style="light" backgroundColor="#000000" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
});

