import React from 'react';
import FinancialDashboardWidget from './sophia/FinancialDashboardWidget';

const SophiaDashboardWidgets: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="lg:col-span-2">
        <FinancialDashboardWidget 
          apis={['Stripe', 'PayPal', 'Square']}
          complianceRules={['PCI-DSS', 'SOC2', 'GDPR']}
        />
      </div>
      {/* Additional widgets can be added here as they're developed */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Transaction Analytics</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Advanced analytics coming soon...</p>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Fraud Detection AI</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">ML-powered fraud detection coming soon...</p>
      </div>
    </div>
  );
};

export default SophiaDashboardWidgets; 