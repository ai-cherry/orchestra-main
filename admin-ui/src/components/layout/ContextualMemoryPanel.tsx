import React from 'react';
import usePersonaStore from '../../store/personaStore';

const ContextualMemoryPanel: React.FC = () => {
  const { getCurrentPersona } = usePersonaStore();
  const currentPersona = getCurrentPersona();
  const currentDomainName = currentPersona?.domain;

  let memoryItems: string[] = [];

  if (currentPersona) {
    switch (currentPersona.id) {
      case 'cherry':
        memoryItems = [
          "Recent health check summary (05/28/2025)",
          "Grocery list for next week",
          "Ideas for weekend trip",
        ];
        break;
      case 'sophia':
        memoryItems = [
          "Active fraud alerts: 3 new",
          "Q2 Financial projection summary",
          "Payment processing optimization report (v1.2)",
        ];
        break;
      case 'karen':
        memoryItems = [
          "Latest compliance document (HIPAA_Update_Q2_2025.pdf)",
          "Clinical trial phase 2 results pending",
          "Research paper on new drug interaction",
        ];
        break;
      default:
        memoryItems = ["No specific contextual memories for this persona."];
    }
  } else {
    memoryItems = ["No active persona selected."];
  }

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-800 border-l border-border dark:border-gray-700 h-full">
      <h3 className="text-lg font-semibold text-foreground dark:text-gray-200 mb-3">
        Contextual Memories
      </h3>
      {currentPersona ? (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            For: <span className="font-medium" style={{ color: currentPersona.color }}>{currentPersona.name}</span> ({currentDomainName} Domain)
          </p>
          {memoryItems.length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
              {memoryItems.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">No relevant memories found.</p>
          )}
        </div>
      ) : (
        <p className="text-sm text-gray-500 dark:text-gray-400">{memoryItems[0]}</p>
      )}
    </div>
  );
};

export default ContextualMemoryPanel; 