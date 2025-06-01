import React from 'react';
import { FileText, CheckCircle, AlertTriangle, Beaker, Lock, FileCheck } from 'lucide-react';

interface ClinicalWorkspaceWidgetProps {
  compliance?: string[];
  tools?: string[];
}

const ClinicalWorkspaceWidget: React.FC<ClinicalWorkspaceWidgetProps> = ({ 
  compliance = ['HIPAA', 'FDA 21 CFR Part 11'], 
  tools = ['eCRF', 'CTMS'] 
}) => {
  // Mock clinical data
  const trialMetrics = {
    activeTrials: 7,
    pendingReviews: 23,
    complianceScore: 98.5,
    documentsProcessed: 156
  };

  const recentActivities = [
    { id: 1, type: 'trial', title: 'Phase III - Drug X23 Update', status: 'active', priority: 'high' },
    { id: 2, type: 'document', title: 'HIPAA Compliance Audit', status: 'pending', priority: 'medium' },
    { id: 3, type: 'qa', title: 'Lab Results Verification', status: 'completed', priority: 'low' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'pending': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
      case 'completed': return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700/30';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'medium': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'low': return <CheckCircle className="h-4 w-4 text-green-500" />;
      default: return null;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Clinical Workspace</h3>
        <div className="flex items-center space-x-2">
          {tools.map((tool, idx) => (
            <span key={idx} className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded">
              {tool}
            </span>
          ))}
        </div>
      </div>

      {/* Trial Monitor */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Beaker className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Trials</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{trialMetrics.activeTrials}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Active</p>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <FileText className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Reviews</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{trialMetrics.pendingReviews}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Pending</p>
        </div>
      </div>

      {/* Compliance Status */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Lock className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Compliance Status</span>
          </div>
          <span className="text-lg font-bold text-green-600 dark:text-green-400">{trialMetrics.complianceScore}%</span>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {compliance.map((rule, idx) => (
            <span key={idx} className="text-xs px-2 py-1 bg-white dark:bg-gray-700 rounded-full text-gray-700 dark:text-gray-300">
              <CheckCircle className="inline h-3 w-3 text-green-500 mr-1" />
              {rule}
            </span>
          ))}
        </div>
      </div>

      {/* Document Vault & QA */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Recent Activities</h4>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            <FileCheck className="inline h-3 w-3 mr-1" />
            {trialMetrics.documentsProcessed} docs this month
          </span>
        </div>
        <div className="space-y-2">
          {recentActivities.map((activity) => (
            <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getPriorityIcon(activity.priority)}
                <div>
                  <p className="text-sm text-gray-900 dark:text-gray-100">{activity.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{activity.type}</p>
                </div>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full capitalize ${getStatusColor(activity.status)}`}>
                {activity.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 grid grid-cols-2 gap-3">
        <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium transition-colors">
          Clinical Dashboard
        </button>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors">
          QA Automation
        </button>
      </div>
    </div>
  );
};

export default ClinicalWorkspaceWidget; 