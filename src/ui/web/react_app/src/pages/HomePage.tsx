import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePersona } from '../contexts/PersonaContext';
import { PersonaSelector } from '../components/persona/PersonaSelector';
import { SearchInput } from '../components/search/SearchInput';
import { QuickActions } from '../components/home/QuickActions';
import { RecentActivity } from '../components/home/RecentActivity';
import { motion } from 'framer-motion';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { currentPersona, accentColor } = usePersona();
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleSearch = (query: string, mode: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}&mode=${mode}`);
  };
  
  return (
    <div className="min-h-screen bg-background-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl font-bold mb-4">
            <span style={{ color: accentColor }}>
              {currentPersona === 'cherry' ? 'Cherry' : 
               currentPersona === 'sophia' ? 'Sophia' : 'Karen'}
            </span> AI
          </h1>
          <p className="text-xl text-text-secondary">
            {currentPersona === 'cherry' ? 'Your friendly AI companion' :
             currentPersona === 'sophia' ? 'Professional business intelligence' :
             'Healthcare expertise at your service'}
          </p>
        </motion.div>
        
        {/* Persona Selector */}
        <div className="flex justify-center mb-8">
          <PersonaSelector />
        </div>
        
        {/* Search Section */}
        <div className="max-w-3xl mx-auto mb-12">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
            placeholder={`Ask ${currentPersona} anything...`}
          />
        </div>
        
        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <QuickActions />
        </div>
        
        {/* Recent Activity */}
        <div className="mt-12">
          <RecentActivity />
        </div>
      </div>
    </div>
  );
};
