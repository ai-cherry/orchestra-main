import React from 'react';
import ClinicalWorkspaceWidget from './karen/ClinicalWorkspaceWidget';

const KarenDashboardWidgets: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="lg:col-span-2">
        <ClinicalWorkspaceWidget 
          compliance={['HIPAA', 'FDA 21 CFR Part 11', 'GCP']}
          tools={['eCRF', 'CTMS', 'EDC']}
        />
      </div>
      {/* Additional widgets can be added here as they're developed */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Drug Interaction Analyzer</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">AI-powered drug interaction analysis coming soon...</p>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Regulatory Compliance Monitor</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Real-time compliance tracking coming soon...</p>
      </div>
    </div>
  );
};

export default KarenDashboardWidgets; 