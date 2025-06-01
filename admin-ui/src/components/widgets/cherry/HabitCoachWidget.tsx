import React from 'react';
import { Target, CheckCircle, Circle, TrendingUp } from 'lucide-react';

interface HabitCoachWidgetProps {
  personality?: 'encouraging' | 'strict' | 'balanced';
}

const HabitCoachWidget: React.FC<HabitCoachWidgetProps> = ({ personality = 'encouraging' }) => {
  // Mock habits data
  const habits = [
    { id: 1, name: 'Morning Meditation', completed: true, streak: 15 },
    { id: 2, name: 'Exercise 30 min', completed: true, streak: 7 },
    { id: 3, name: 'Read 20 pages', completed: false, streak: 3 },
    { id: 4, name: 'Drink 8 glasses water', completed: true, streak: 21 },
  ];

  const completedCount = habits.filter(h => h.completed).length;
  const completionRate = (completedCount / habits.length) * 100;

  const getCoachMessage = () => {
    switch (personality) {
      case 'encouraging':
        return completionRate >= 75 
          ? "Amazing work! You're crushing it today! 🎉"
          : "You're doing great! Keep going! 💪";
      case 'strict':
        return completionRate >= 75
          ? "Good. Now maintain this consistency."
          : "You can do better. Focus on completing all habits.";
      case 'balanced':
        return completionRate >= 75
          ? "Excellent progress today! Well done."
          : "Good effort so far. Let's complete the remaining habits.";
      default:
        return "Keep up the good work!";
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Habit Coach</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">{personality} mode</span>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Today's Progress</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{completedCount}/{habits.length}</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-red-500 to-pink-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>

      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 mb-4">
        <p className="text-sm text-gray-700 dark:text-gray-300 text-center italic">
          "{getCoachMessage()}"
        </p>
      </div>

      <div className="space-y-3">
        {habits.map((habit) => (
          <div key={habit.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center space-x-3">
              {habit.completed ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <Circle className="h-5 w-5 text-gray-400" />
              )}
              <span className={`text-sm ${habit.completed ? 'text-gray-500 line-through' : 'text-gray-900 dark:text-gray-100'}`}>
                {habit.name}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-orange-500" />
              <span className="text-xs text-gray-600 dark:text-gray-400">{habit.streak} days</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button className="w-full px-4 py-2 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 text-white rounded-md text-sm font-medium transition-all">
          View Habit Analytics
        </button>
      </div>
    </div>
  );
};

export default HabitCoachWidget; 