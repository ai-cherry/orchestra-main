import React from 'react';
import HealthTrackerWidget from './cherry/HealthTrackerWidget';
import HabitCoachWidget from './cherry/HabitCoachWidget';
import MediaGeneratorWidget from './cherry/MediaGeneratorWidget';

const CherryDashboardWidgets: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div className="md:col-span-1">
        <HealthTrackerWidget syncWith="Apple Health" />
      </div>
      <div className="md:col-span-1">
        <HabitCoachWidget personality="encouraging" />
      </div>
      <div className="md:col-span-1 xl:col-span-1">
        <MediaGeneratorWidget api="DALL-E" />
      </div>
    </div>
  );
};

export default CherryDashboardWidgets; 