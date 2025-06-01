import React from 'react';
import usePersonaStore from '../../store/personaStore';

const DomainSwitcher: React.FC = () => {
  const { personas, activePersonaId, setActivePersona } = usePersonaStore();

  return (
    <div className="flex flex-col space-y-1 p-2">
      {personas.map((persona) => {
        const isActive = persona.id === activePersonaId;
        // Use persona.color directly
        const activeBgColor = persona.color;

        return (
          <button
            key={persona.id}
            onClick={() => setActivePersona(persona.id)}
            className={`
              w-full text-left px-3 py-2 rounded-md text-sm font-medium
              transition-all duration-150 ease-in-out
              focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-gray-800 focus:ring-indigo-500
              ${
                isActive
                  ? 'text-white shadow-md' // Active button: white text, shadow
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100'
              }
            `}
            style={isActive ? { backgroundColor: activeBgColor } : {}}
          >
            {persona.name}
          </button>
        );
      })}
    </div>
  );
};

export default DomainSwitcher;
