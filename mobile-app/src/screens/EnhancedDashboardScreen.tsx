import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface DashboardMetrics {
  totalTasks: number;
  completedTasks: number;
  activeProjects: number;
  recentActivity: string[];
}

export default function DashboardScreen() {
  const navigation = useNavigation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalTasks: 0,
    completedTasks: 0,
    activeProjects: 0,
    recentActivity: [],
  });

  useEffect(() => {
    checkAuthentication();
    loadDashboardData();
  }, []);

  const checkAuthentication = async () => {
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      
      if (hasHardware && isEnrolled) {
        const result = await LocalAuthentication.authenticateAsync({
          promptMessage: 'Authenticate to access Orchestra AI',
          fallbackLabel: 'Use Passcode',
        });
        
        if (result.success) {
          setIsAuthenticated(true);
        } else {
          Alert.alert('Authentication Failed', 'Please try again');
        }
      } else {
        // Fallback to simple authentication
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setIsAuthenticated(true); // Fallback for development
    } finally {
      setIsLoading(false);
    }
  };

  const loadDashboardData = async () => {
    try {
      // Load cached data
      const cachedData = await AsyncStorage.getItem('dashboardMetrics');
      if (cachedData) {
        setMetrics(JSON.parse(cachedData));
      }

      // Simulate API call to load real data
      // In production, this would call your Orchestra AI backend
      const mockData: DashboardMetrics = {
        totalTasks: 24,
        completedTasks: 18,
        activeProjects: 5,
        recentActivity: [
          'Updated Linear issue #123',
          'Synced with GitHub repository',
          'Created new Notion page',
          'Completed Asana task',
          'AI chat session completed',
        ],
      };

      setMetrics(mockData);
      await AsyncStorage.setItem('dashboardMetrics', JSON.stringify(mockData));
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const features = [
    {
      title: 'AI Chat',
      description: 'Chat with Orchestra AI',
      screen: 'Chat',
      icon: '🤖',
      color: '#007AFF',
    },
    {
      title: 'Voice Commands',
      description: 'Voice-powered interactions',
      screen: 'Voice',
      icon: '🎤',
      color: '#34C759',
    },
    {
      title: 'Linear Tasks',
      description: 'Manage Linear issues',
      screen: 'Linear',
      icon: '📋',
      color: '#5856D6',
    },
    {
      title: 'GitHub Projects',
      description: 'Repository management',
      screen: 'GitHub',
      icon: '🐙',
      color: '#FF9500',
    },
    {
      title: 'Asana Tasks',
      description: 'Project coordination',
      screen: 'Asana',
      icon: '✅',
      color: '#FF3B30',
    },
    {
      title: 'Notion Docs',
      description: 'Knowledge management',
      screen: 'Notion',
      icon: '📝',
      color: '#000000',
    },
    {
      title: 'Analytics',
      description: 'Performance insights',
      screen: 'Analytics',
      icon: '📊',
      color: '#AF52DE',
    },
    {
      title: 'Settings',
      description: 'App configuration',
      screen: 'Settings',
      icon: '⚙️',
      color: '#8E8E93',
    },
  ];

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading Orchestra AI...</Text>
      </View>
    );
  }

  if (!isAuthenticated) {
    return (
      <View style={styles.authContainer}>
        <Text style={styles.authTitle}>Authentication Required</Text>
        <Text style={styles.authSubtitle}>
          Please authenticate to access Orchestra AI
        </Text>
        <TouchableOpacity style={styles.authButton} onPress={checkAuthentication}>
          <Text style={styles.authButtonText}>Authenticate</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Orchestra AI</Text>
        <Text style={styles.subtitle}>Your Personal AI Assistant</Text>
      </View>

      {/* Metrics Cards */}
      <View style={styles.metricsContainer}>
        <View style={styles.metricCard}>
          <Text style={styles.metricNumber}>{metrics.totalTasks}</Text>
          <Text style={styles.metricLabel}>Total Tasks</Text>
        </View>
        <View style={styles.metricCard}>
          <Text style={styles.metricNumber}>{metrics.completedTasks}</Text>
          <Text style={styles.metricLabel}>Completed</Text>
        </View>
        <View style={styles.metricCard}>
          <Text style={styles.metricNumber}>{metrics.activeProjects}</Text>
          <Text style={styles.metricLabel}>Projects</Text>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
      </View>

      <View style={styles.featuresContainer}>
        {features.map((feature, index) => (
          <TouchableOpacity
            key={index}
            style={[styles.featureCard, { borderLeftColor: feature.color }]}
            onPress={() => {
              if (feature.screen) {
                navigation.navigate(feature.screen as never);
              } else {
                Alert.alert('Coming Soon', `${feature.title} feature is in development`);
              }
            }}
          >
            <View style={styles.featureIcon}>
              <Text style={styles.featureIconText}>{feature.icon}</Text>
            </View>
            <View style={styles.featureContent}>
              <Text style={styles.featureTitle}>{feature.title}</Text>
              <Text style={styles.featureDescription}>{feature.description}</Text>
            </View>
            <Text style={styles.featureArrow}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recent Activity */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
      </View>

      <View style={styles.activityContainer}>
        {metrics.recentActivity.map((activity, index) => (
          <View key={index} style={styles.activityItem}>
            <View style={styles.activityDot} />
            <Text style={styles.activityText}>{activity}</Text>
          </View>
        ))}
      </View>

      {/* Bottom Spacing */}
      <View style={styles.bottomSpacing} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    marginTop: 16,
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    padding: 20,
  },
  authTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  authSubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 32,
  },
  authButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  authButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    padding: 20,
    paddingTop: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
  },
  metricsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  metricNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  metricLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  sectionHeader: {
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  featuresContainer: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  featureCard: {
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderLeftWidth: 4,
  },
  featureIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2C2C2E',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  featureIconText: {
    fontSize: 20,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  featureArrow: {
    fontSize: 20,
    color: '#8E8E93',
  },
  activityContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  activityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007AFF',
    marginRight: 12,
  },
  activityText: {
    fontSize: 14,
    color: '#FFFFFF',
    flex: 1,
  },
  bottomSpacing: {
    height: 40,
  },
});

