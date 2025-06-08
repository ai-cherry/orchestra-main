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
