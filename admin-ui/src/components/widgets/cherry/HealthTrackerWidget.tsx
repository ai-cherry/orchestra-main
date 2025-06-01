import React from 'react';
import { Activity, Heart, TrendingUp, Calendar } from 'lucide-react';

interface HealthTrackerWidgetProps {
  syncWith?: string;
}

const HealthTrackerWidget: React.FC<HealthTrackerWidgetProps> = ({ syncWith = 'Apple Health' }) => {
  // Mock data for demonstration
  const healthMetrics = {
    steps: 8432,
    heartRate: 72,
    sleep: 7.5,
    calories: 2150
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Health Tracker</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">Sync: {syncWith}</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <Activity className="h-5 w-5 text-red-600 dark:text-red-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Steps</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-2">{healthMetrics.steps.toLocaleString()}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Goal: 10,000</p>
        </div>

        <div className="bg-pink-50 dark:bg-pink-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <Heart className="h-5 w-5 text-pink-600 dark:text-pink-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Heart Rate</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-2">{healthMetrics.heartRate}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">bpm</p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <Calendar className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Sleep</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-2">{healthMetrics.sleep}h</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Last night</p>
        </div>

        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Calories</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-2">{healthMetrics.calories}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">kcal burned</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium transition-colors">
          View Detailed Report
        </button>
      </div>
    </div>
  );
};

export default HealthTrackerWidget; 