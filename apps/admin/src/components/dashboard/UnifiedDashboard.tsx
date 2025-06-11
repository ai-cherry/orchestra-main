import React, { useState, useEffect } from 'react';
import { useContextManager } from '../contexts/ContextManagerContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import ServiceManager from '../services/ServiceManager';

interface UnifiedDashboardProps {
  className?: string;
}

interface DashboardData {
  linear: {
    projects: any[];
    status: string;
  };
  github: {
    projects: any[];
    status: string;
  };
  asana: {
    projects: any[];
    status: string;
  };
  recentActivity: any[];
  metrics: {
    totalTasks: number;
    completedTasks: number;
    pendingTasks: number;
    productivity: number;
  };
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({ className = '' }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addContext } = useContextManager();
  const { isConnected, subscribe } = useWebSocket();

  useEffect(() => {
    loadDashboardData();
    
    // Subscribe to real-time updates
    if (isConnected) {
      subscribe('dashboard_update', handleDashboardUpdate);
    }
  }, [isConnected]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const serviceManager = ServiceManager.getInstance();
      const data = await serviceManager.getUnifiedDashboard();
      
      // Calculate metrics
      const metrics = calculateMetrics(data);
      
      setDashboardData({
        ...data,
        recentActivity: [], // Will be populated from real-time updates
        metrics
      });

      // Add to context for AI learning
      addContext(
        `Dashboard loaded with ${metrics.totalTasks} total tasks across Linear, GitHub, and Asana`,
        'task',
        { source: 'unified_dashboard', metrics }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleDashboardUpdate = (data: any) => {
    // Handle real-time dashboard updates
    setDashboardData(prev => {
      if (!prev) return prev;
      
      return {
        ...prev,
        recentActivity: [data, ...prev.recentActivity.slice(0, 9)] // Keep last 10 activities
      };
    });
  };

  const calculateMetrics = (data: any) => {
    let totalTasks = 0;
    let completedTasks = 0;

    // Count Linear tasks
    data.linear.projects.forEach((project: any) => {
      project.issues?.forEach((issue: any) => {
        totalTasks++;
        if (issue.state === 'Done' || issue.state === 'Completed') {
          completedTasks++;
        }
      });
    });

    // Count GitHub issues
    data.github.projects.forEach((project: any) => {
      project.items?.forEach((item: any) => {
        totalTasks++;
        if (item.state === 'CLOSED') {
          completedTasks++;
        }
      });
    });

    // Count Asana tasks
    data.asana.projects.forEach((project: any) => {
      project.tasks?.forEach((task: any) => {
        totalTasks++;
        if (task.completed) {
          completedTasks++;
        }
      });
    });

    const pendingTasks = totalTasks - completedTasks;
    const productivity = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

    return {
      totalTasks,
      completedTasks,
      pendingTasks,
      productivity: Math.round(productivity)
    };
  };

  const handleCreateTask = async () => {
    try {
      const serviceManager = ServiceManager.getInstance();
      const title = prompt('Enter task title:');
      const description = prompt('Enter task description:');
      
      if (title && description) {
        await serviceManager.createTaskAcrossAllPlatforms(title, description);
        addContext(
          `Created task "${title}" across all platforms`,
          'task',
          { action: 'create', title, description }
        );
        loadDashboardData(); // Refresh dashboard
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    }
  };

  const handleSearch = async () => {
    try {
      const serviceManager = ServiceManager.getInstance();
      const query = prompt('Enter search query:');
      
      if (query) {
        const results = await serviceManager.searchAcrossAllPlatforms(query);
        addContext(
          `Searched for "${query}" across all platforms`,
          'search',
          { query, results }
        );
        
        // Display results in a modal or new component
        console.log('Search results:', results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search');
    }
  };

  if (loading) {
    return (
      <div className={`unified-dashboard ${className}`}>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading unified dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`unified-dashboard ${className}`}>
        <div className="error-message">
          <h3>Dashboard Error</h3>
          <p>{error}</p>
          <button onClick={loadDashboardData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <div className={`unified-dashboard ${className}`}>
      <div className="dashboard-header">
        <h2>Unified Dashboard</h2>
        <div className="dashboard-actions">
          <button onClick={handleCreateTask} className="create-task-btn">
            Create Task
          </button>
          <button onClick={handleSearch} className="search-btn">
            Search All
          </button>
          <button onClick={loadDashboardData} className="refresh-btn">
            Refresh
          </button>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Tasks</h3>
          <div className="metric-value">{dashboardData.metrics.totalTasks}</div>
        </div>
        <div className="metric-card">
          <h3>Completed</h3>
          <div className="metric-value">{dashboardData.metrics.completedTasks}</div>
        </div>
        <div className="metric-card">
          <h3>Pending</h3>
          <div className="metric-value">{dashboardData.metrics.pendingTasks}</div>
        </div>
        <div className="metric-card">
          <h3>Productivity</h3>
          <div className="metric-value">{dashboardData.metrics.productivity}%</div>
        </div>
      </div>

      <div className="platforms-grid">
        <div className="platform-section">
          <h3>Linear Projects</h3>
          <div className="platform-status">
            Status: {dashboardData.linear.status === 'fulfilled' ? '✅ Connected' : '❌ Error'}
          </div>
          <div className="project-list">
            {dashboardData.linear.projects.slice(0, 3).map((project: any) => (
              <div key={project.id} className="project-item">
                <h4>{project.name}</h4>
                <p>{project.issues?.length || 0} issues</p>
              </div>
            ))}
          </div>
        </div>

        <div className="platform-section">
          <h3>GitHub Projects</h3>
          <div className="platform-status">
            Status: {dashboardData.github.status === 'fulfilled' ? '✅ Connected' : '❌ Error'}
          </div>
          <div className="project-list">
            {dashboardData.github.projects.slice(0, 3).map((project: any) => (
              <div key={project.id} className="project-item">
                <h4>{project.title}</h4>
                <p>{project.items?.length || 0} items</p>
              </div>
            ))}
          </div>
        </div>

        <div className="platform-section">
          <h3>Asana Projects</h3>
          <div className="platform-status">
            Status: {dashboardData.asana.status === 'fulfilled' ? '✅ Connected' : '❌ Error'}
          </div>
          <div className="project-list">
            {dashboardData.asana.projects.slice(0, 3).map((project: any) => (
              <div key={project.gid} className="project-item">
                <h4>{project.name}</h4>
                <p>{project.tasks?.length || 0} tasks</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {dashboardData.recentActivity.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            {dashboardData.recentActivity.map((activity: any, index: number) => (
              <div key={index} className="activity-item">
                <div className="activity-time">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </div>
                <div className="activity-description">
                  {activity.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .unified-dashboard {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
        }

        .dashboard-actions {
          display: flex;
          gap: 10px;
        }

        .dashboard-actions button {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          background: #3B82F6;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }

        .dashboard-actions button:hover {
          background: #2563EB;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .metric-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          text-align: center;
        }

        .metric-card h3 {
          margin: 0 0 10px 0;
          color: #6B7280;
          font-size: 14px;
          font-weight: 500;
        }

        .metric-value {
          font-size: 32px;
          font-weight: bold;
          color: #1F2937;
        }

        .platforms-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .platform-section {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .platform-section h3 {
          margin: 0 0 10px 0;
          color: #1F2937;
        }

        .platform-status {
          margin-bottom: 15px;
          font-size: 14px;
        }

        .project-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .project-item {
          padding: 10px;
          background: #F9FAFB;
          border-radius: 6px;
        }

        .project-item h4 {
          margin: 0 0 5px 0;
          font-size: 14px;
          color: #1F2937;
        }

        .project-item p {
          margin: 0;
          font-size: 12px;
          color: #6B7280;
        }

        .recent-activity {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .recent-activity h3 {
          margin: 0 0 15px 0;
          color: #1F2937;
        }

        .activity-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .activity-item {
          display: flex;
          gap: 15px;
          padding: 10px;
          background: #F9FAFB;
          border-radius: 6px;
        }

        .activity-time {
          font-size: 12px;
          color: #6B7280;
          white-space: nowrap;
        }

        .activity-description {
          font-size: 14px;
          color: #1F2937;
        }

        .loading-spinner {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #3B82F6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          text-align: center;
          padding: 40px;
        }

        .error-message h3 {
          color: #DC2626;
          margin-bottom: 10px;
        }

        .retry-button {
          padding: 10px 20px;
          background: #3B82F6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          margin-top: 15px;
        }

        .retry-button:hover {
          background: #2563EB;
        }
      `}</style>
    </div>
  );
};

export default UnifiedDashboard;

