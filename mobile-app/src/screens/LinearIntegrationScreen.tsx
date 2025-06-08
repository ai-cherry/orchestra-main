import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface LinearIssue {
  id: string;
  title: string;
  description: string;
  status: 'Todo' | 'In Progress' | 'Done' | 'Cancelled';
  priority: 'Low' | 'Medium' | 'High' | 'Urgent';
  assignee?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface LinearTeam {
  id: string;
  name: string;
  description: string;
  issueCount: number;
}

export default function LinearIntegrationScreen() {
  const [issues, setIssues] = useState<LinearIssue[]>([]);
  const [teams, setTeams] = useState<LinearTeam[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'assigned' | 'created'>('all');

  useEffect(() => {
    loadLinearData();
  }, []);

  const loadLinearData = async () => {
    try {
      setIsLoading(true);
      
      // Load cached data first
      const cachedIssues = await AsyncStorage.getItem('linearIssues');
      const cachedTeams = await AsyncStorage.getItem('linearTeams');
      
      if (cachedIssues) {
        setIssues(JSON.parse(cachedIssues));
      }
      if (cachedTeams) {
        setTeams(JSON.parse(cachedTeams));
      }

      // Simulate API call to Linear
      // In production, this would use the Linear GraphQL API
      const mockIssues: LinearIssue[] = [
        {
          id: 'ORG-123',
          title: 'Implement mobile app authentication',
          description: 'Add biometric authentication to the mobile app for enhanced security',
          status: 'In Progress',
          priority: 'High',
          assignee: 'You',
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date('2024-01-20'),
        },
        {
          id: 'ORG-124',
          title: 'Optimize API response times',
          description: 'Improve backend API performance for better user experience',
          status: 'Todo',
          priority: 'Medium',
          assignee: 'Team Lead',
          createdAt: new Date('2024-01-18'),
          updatedAt: new Date('2024-01-18'),
        },
        {
          id: 'ORG-125',
          title: 'Design new dashboard layout',
          description: 'Create a more intuitive dashboard design for better UX',
          status: 'Done',
          priority: 'Low',
          assignee: 'Designer',
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date('2024-01-19'),
        },
        {
          id: 'ORG-126',
          title: 'Fix critical security vulnerability',
          description: 'Address security issue found in authentication system',
          status: 'Todo',
          priority: 'Urgent',
          assignee: 'You',
          createdAt: new Date('2024-01-21'),
          updatedAt: new Date('2024-01-21'),
        },
      ];

      const mockTeams: LinearTeam[] = [
        {
          id: 'team-1',
          name: 'Engineering',
          description: 'Core development team',
          issueCount: 15,
        },
        {
          id: 'team-2',
          name: 'Design',
          description: 'UI/UX design team',
          issueCount: 8,
        },
        {
          id: 'team-3',
          name: 'Product',
          description: 'Product management team',
          issueCount: 12,
        },
      ];

      setIssues(mockIssues);
      setTeams(mockTeams);

      // Cache the data
      await AsyncStorage.setItem('linearIssues', JSON.stringify(mockIssues));
      await AsyncStorage.setItem('linearTeams', JSON.stringify(mockTeams));

    } catch (error) {
      console.error('Error loading Linear data:', error);
      Alert.alert('Error', 'Failed to load Linear data. Please try again.');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadLinearData();
  };

  const getStatusColor = (status: LinearIssue['status']) => {
    switch (status) {
      case 'Todo': return '#8E8E93';
      case 'In Progress': return '#007AFF';
      case 'Done': return '#34C759';
      case 'Cancelled': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const getPriorityColor = (priority: LinearIssue['priority']) => {
    switch (priority) {
      case 'Low': return '#34C759';
      case 'Medium': return '#FF9500';
      case 'High': return '#FF3B30';
      case 'Urgent': return '#AF52DE';
      default: return '#8E8E93';
    }
  };

  const filteredIssues = issues.filter(issue => {
    switch (selectedFilter) {
      case 'assigned':
        return issue.assignee === 'You';
      case 'created':
        return issue.assignee === 'You'; // In real app, filter by creator
      default:
        return true;
    }
  });

  const createNewIssue = () => {
    Alert.alert(
      'Create New Issue',
      'This would open the issue creation form in the full app.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Create', onPress: () => console.log('Create issue') },
      ]
    );
  };

  const openIssue = (issue: LinearIssue) => {
    Alert.alert(
      issue.title,
      `${issue.description}\n\nStatus: ${issue.status}\nPriority: ${issue.priority}\nAssignee: ${issue.assignee}`,
      [
        { text: 'Close', style: 'cancel' },
        { text: 'Edit', onPress: () => console.log('Edit issue', issue.id) },
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading Linear data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Linear Integration</Text>
        <TouchableOpacity style={styles.createButton} onPress={createNewIssue}>
          <Text style={styles.createButtonText}>+ New Issue</Text>
        </TouchableOpacity>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        {[
          { key: 'all', label: 'All Issues' },
          { key: 'assigned', label: 'Assigned to Me' },
          { key: 'created', label: 'Created by Me' },
        ].map((filter) => (
          <TouchableOpacity
            key={filter.key}
            style={[
              styles.filterTab,
              selectedFilter === filter.key && styles.activeFilterTab,
            ]}
            onPress={() => setSelectedFilter(filter.key as any)}
          >
            <Text
              style={[
                styles.filterTabText,
                selectedFilter === filter.key && styles.activeFilterTabText,
              ]}
            >
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Teams Overview */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Teams</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {teams.map((team) => (
            <View key={team.id} style={styles.teamCard}>
              <Text style={styles.teamName}>{team.name}</Text>
              <Text style={styles.teamDescription}>{team.description}</Text>
              <Text style={styles.teamIssueCount}>{team.issueCount} issues</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Issues List */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          Issues ({filteredIssues.length})
        </Text>
        <ScrollView
          style={styles.issuesList}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {filteredIssues.map((issue) => (
            <TouchableOpacity
              key={issue.id}
              style={styles.issueCard}
              onPress={() => openIssue(issue)}
            >
              <View style={styles.issueHeader}>
                <Text style={styles.issueId}>{issue.id}</Text>
                <View style={styles.issueBadges}>
                  <View
                    style={[
                      styles.priorityBadge,
                      { backgroundColor: getPriorityColor(issue.priority) },
                    ]}
                  >
                    <Text style={styles.badgeText}>{issue.priority}</Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: getStatusColor(issue.status) },
                    ]}
                  >
                    <Text style={styles.badgeText}>{issue.status}</Text>
                  </View>
                </View>
              </View>
              
              <Text style={styles.issueTitle}>{issue.title}</Text>
              <Text style={styles.issueDescription} numberOfLines={2}>
                {issue.description}
              </Text>
              
              <View style={styles.issueFooter}>
                <Text style={styles.issueAssignee}>
                  Assigned to: {issue.assignee || 'Unassigned'}
                </Text>
                <Text style={styles.issueDate}>
                  Updated {issue.updatedAt.toLocaleDateString()}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </View>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  createButton: {
    backgroundColor: '#5856D6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  createButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  filterTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 12,
    backgroundColor: '#1C1C1E',
  },
  activeFilterTab: {
    backgroundColor: '#007AFF',
  },
  filterTabText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '500',
  },
  activeFilterTabText: {
    color: '#FFFFFF',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  teamCard: {
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginLeft: 20,
    marginRight: 8,
    width: 160,
  },
  teamName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  teamDescription: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 8,
  },
  teamIssueCount: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  issuesList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  issueCard: {
    backgroundColor: '#1C1C1E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  issueHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  issueId: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  issueBadges: {
    flexDirection: 'row',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  issueTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  issueDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 12,
  },
  issueFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  issueAssignee: {
    fontSize: 12,
    color: '#8E8E93',
  },
  issueDate: {
    fontSize: 12,
    color: '#8E8E93',
  },
});

