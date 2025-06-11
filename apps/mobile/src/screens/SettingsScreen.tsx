import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  Share,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as LocalAuthentication from 'expo-local-authentication';

interface SettingsItem {
  id: string;
  title: string;
  description?: string;
  type: 'toggle' | 'action' | 'navigation';
  value?: boolean;
  onPress?: () => void;
  icon: string;
}

export default function SettingsScreen() {
  const [biometricEnabled, setBiometricEnabled] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkModeEnabled, setDarkModeEnabled] = useState(true);
  const [offlineModeEnabled, setOfflineModeEnabled] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await AsyncStorage.getItem('appSettings');
      if (settings) {
        const parsedSettings = JSON.parse(settings);
        setBiometricEnabled(parsedSettings.biometricEnabled ?? true);
        setVoiceEnabled(parsedSettings.voiceEnabled ?? true);
        setNotificationsEnabled(parsedSettings.notificationsEnabled ?? true);
        setDarkModeEnabled(parsedSettings.darkModeEnabled ?? true);
        setOfflineModeEnabled(parsedSettings.offlineModeEnabled ?? true);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = async (newSettings: any) => {
    try {
      const currentSettings = {
        biometricEnabled,
        voiceEnabled,
        notificationsEnabled,
        darkModeEnabled,
        offlineModeEnabled,
        ...newSettings,
      };
      await AsyncStorage.setItem('appSettings', JSON.stringify(currentSettings));
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  const toggleBiometric = async (value: boolean) => {
    if (value) {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      
      if (!hasHardware || !isEnrolled) {
        Alert.alert(
          'Biometric Authentication Unavailable',
          'Please set up biometric authentication in your device settings first.'
        );
        return;
      }
    }
    
    setBiometricEnabled(value);
    saveSettings({ biometricEnabled: value });
  };

  const clearCache = async () => {
    Alert.alert(
      'Clear Cache',
      'This will remove all cached data including offline content. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.multiRemove([
                'dashboardMetrics',
                'linearIssues',
                'linearTeams',
                'chatHistory',
                'offlineData',
              ]);
              Alert.alert('Success', 'Cache cleared successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear cache');
            }
          },
        },
      ]
    );
  };

  const exportData = async () => {
    try {
      const allKeys = await AsyncStorage.getAllKeys();
      const allData = await AsyncStorage.multiGet(allKeys);
      const exportData = Object.fromEntries(allData);
      
      await Share.share({
        message: JSON.stringify(exportData, null, 2),
        title: 'Orchestra AI Data Export',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to export data');
    }
  };

  const resetApp = () => {
    Alert.alert(
      'Reset App',
      'This will reset all settings and data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.clear();
              Alert.alert('Success', 'App has been reset. Please restart the app.');
            } catch (error) {
              Alert.alert('Error', 'Failed to reset app');
            }
          },
        },
      ]
    );
  };

  const settingsSections = [
    {
      title: 'Security',
      items: [
        {
          id: 'biometric',
          title: 'Biometric Authentication',
          description: 'Use Face ID or fingerprint to unlock the app',
          type: 'toggle' as const,
          value: biometricEnabled,
          onPress: () => toggleBiometric(!biometricEnabled),
          icon: '🔒',
        },
      ],
    },
    {
      title: 'Features',
      items: [
        {
          id: 'voice',
          title: 'Voice Commands',
          description: 'Enable voice-powered interactions',
          type: 'toggle' as const,
          value: voiceEnabled,
          onPress: () => {
            setVoiceEnabled(!voiceEnabled);
            saveSettings({ voiceEnabled: !voiceEnabled });
          },
          icon: '🎤',
        },
        {
          id: 'notifications',
          title: 'Push Notifications',
          description: 'Receive updates and reminders',
          type: 'toggle' as const,
          value: notificationsEnabled,
          onPress: () => {
            setNotificationsEnabled(!notificationsEnabled);
            saveSettings({ notificationsEnabled: !notificationsEnabled });
          },
          icon: '🔔',
        },
        {
          id: 'offline',
          title: 'Offline Mode',
          description: 'Cache data for offline access',
          type: 'toggle' as const,
          value: offlineModeEnabled,
          onPress: () => {
            setOfflineModeEnabled(!offlineModeEnabled);
            saveSettings({ offlineModeEnabled: !offlineModeEnabled });
          },
          icon: '📱',
        },
      ],
    },
    {
      title: 'Appearance',
      items: [
        {
          id: 'darkMode',
          title: 'Dark Mode',
          description: 'Use dark theme (always enabled)',
          type: 'toggle' as const,
          value: darkModeEnabled,
          onPress: () => {
            // Dark mode is always enabled in this app
            Alert.alert('Info', 'Dark mode is always enabled in Orchestra AI');
          },
          icon: '🌙',
        },
      ],
    },
    {
      title: 'Data',
      items: [
        {
          id: 'clearCache',
          title: 'Clear Cache',
          description: 'Remove cached data and offline content',
          type: 'action' as const,
          onPress: clearCache,
          icon: '🗑️',
        },
        {
          id: 'exportData',
          title: 'Export Data',
          description: 'Export your data for backup',
          type: 'action' as const,
          onPress: exportData,
          icon: '📤',
        },
      ],
    },
    {
      title: 'About',
      items: [
        {
          id: 'version',
          title: 'Version',
          description: '1.0.0 (Build 1)',
          type: 'action' as const,
          onPress: () => Alert.alert('Orchestra AI', 'Version 1.0.0\nBuild 1\n\nYour personal AI assistant'),
          icon: 'ℹ️',
        },
        {
          id: 'support',
          title: 'Support',
          description: 'Get help and report issues',
          type: 'action' as const,
          onPress: () => Alert.alert('Support', 'For support, please contact your administrator.'),
          icon: '❓',
        },
      ],
    },
    {
      title: 'Danger Zone',
      items: [
        {
          id: 'reset',
          title: 'Reset App',
          description: 'Reset all settings and data',
          type: 'action' as const,
          onPress: resetApp,
          icon: '⚠️',
        },
      ],
    },
  ];

  const renderSettingItem = (item: SettingsItem) => {
    return (
      <TouchableOpacity
        key={item.id}
        style={styles.settingItem}
        onPress={item.onPress}
        disabled={item.type === 'toggle'}
      >
        <View style={styles.settingIcon}>
          <Text style={styles.settingIconText}>{item.icon}</Text>
        </View>
        
        <View style={styles.settingContent}>
          <Text style={styles.settingTitle}>{item.title}</Text>
          {item.description && (
            <Text style={styles.settingDescription}>{item.description}</Text>
          )}
        </View>
        
        {item.type === 'toggle' && (
          <Switch
            value={item.value}
            onValueChange={item.onPress}
            trackColor={{ false: '#2C2C2E', true: '#007AFF' }}
            thumbColor="#FFFFFF"
          />
        )}
        
        {item.type === 'action' && (
          <Text style={styles.settingArrow}>›</Text>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Customize your Orchestra AI experience</Text>
      </View>

      {settingsSections.map((section, sectionIndex) => (
        <View key={sectionIndex} style={styles.section}>
          <Text style={[
            styles.sectionTitle,
            section.title === 'Danger Zone' && styles.dangerSectionTitle,
          ]}>
            {section.title}
          </Text>
          
          <View style={[
            styles.sectionContent,
            section.title === 'Danger Zone' && styles.dangerSection,
          ]}>
            {section.items.map(renderSettingItem)}
          </View>
        </View>
      ))}

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Orchestra AI - Your Personal AI Assistant
        </Text>
        <Text style={styles.footerSubtext}>
          Made with ❤️ for productivity and creativity
        </Text>
      </View>
    </ScrollView>
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
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  dangerSectionTitle: {
    color: '#FF3B30',
  },
  sectionContent: {
    backgroundColor: '#1C1C1E',
    marginHorizontal: 20,
    borderRadius: 12,
  },
  dangerSection: {
    borderWidth: 1,
    borderColor: '#FF3B30',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  settingIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#2C2C2E',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  settingIconText: {
    fontSize: 16,
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  settingArrow: {
    fontSize: 20,
    color: '#8E8E93',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
    marginBottom: 40,
  },
  footerText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

