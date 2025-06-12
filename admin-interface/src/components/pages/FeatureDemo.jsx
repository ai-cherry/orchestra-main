import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AnimatedCard, AnimatedButton, AnimatedContainer } from '../ui/AnimatedCard';
import { VoiceInput } from '../ui/VoiceInput';
import { usePersonaAnimations, usePageTransition } from '../../hooks/usePersonaAnimations';

export const FeatureDemo = ({ persona = 'cherry' }) => {
  const [activeFeature, setActiveFeature] = useState('animations');
  const [commandResults, setCommandResults] = useState([]);
  const [demoData, setDemoData] = useState({
    animations: { tested: false, result: null },
    voice: { tested: false, result: null },
    llm: { tested: false, result: null },
    commands: { tested: false, result: null },
    context: { tested: false, result: null }
  });

  const pageTransition = usePageTransition();
  const personaAnimations = usePersonaAnimations(persona);

  const features = [
    {
      id: 'animations',
      name: 'Enhanced Animations',
      icon: '✨',
      description: 'Persona-specific animations with Framer Motion',
      status: 'implemented'
    },
    {
      id: 'voice',
      name: 'Voice Recognition',
      icon: '🎤',
      description: 'Web Speech API with MCP integration',
      status: 'implemented'
    },
    {
      id: 'llm',
      name: 'LLM Integration',
      icon: '🤖',
      description: 'OpenRouter + direct provider connections',
      status: 'ready'
    },
    {
      id: 'commands',
      name: 'Natural Language Commands',
      icon: '💬',
      description: 'Command parsing with UI action execution',
      status: 'ready'
    },
    {
      id: 'context',
      name: 'Advanced Context',
      icon: '🧠',
      description: 'Enhanced memory system with cross-persona collaboration',
      status: 'ready'
    }
  ];

  const handleVoiceCommand = (commandData) => {
    const newResult = {
      id: Date.now(),
      type: 'voice',
      data: commandData,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setCommandResults(prev => [newResult, ...prev.slice(0, 4)]);
    setDemoData(prev => ({
      ...prev,
      voice: { tested: true, result: commandData }
    }));
  };

  const testAnimations = () => {
    setDemoData(prev => ({
      ...prev,
      animations: { 
        tested: true, 
        result: `${persona.charAt(0).toUpperCase() + persona.slice(1)} animations active` 
      }
    }));
  };

  const testFeature = async (featureId) => {
    setActiveFeature(featureId);
    
    // Simulate feature testing
    const mockResults = {
      llm: `LLM integration test for ${persona} - Response generated successfully`,
      commands: `Natural language command processed: "show me the dashboard"`,
      context: `Memory context accessed - 5-tier architecture operational`
    };

    if (mockResults[featureId]) {
      setDemoData(prev => ({
        ...prev,
        [featureId]: { tested: true, result: mockResults[featureId] }
      }));
    }
  };

  const renderFeatureContent = () => {
    switch (activeFeature) {
      case 'animations':
        return (
          <AnimatedContainer persona={persona} className="feature-content">
            <h3>Enhanced Animations Demo</h3>
            <p>This page demonstrates persona-specific animations using Framer Motion.</p>
            
            <div className="animation-showcase">
              <AnimatedCard persona={persona} className="demo-card">
                <h4>{persona.charAt(0).toUpperCase() + persona.slice(1)} Animation Style</h4>
                <p>Each persona has unique animation characteristics:</p>
                <ul>
                  <li><strong>Cherry:</strong> Spring animations with scale effects</li>
                  <li><strong>Sophia:</strong> Smooth slide transitions</li>
                  <li><strong>Karen:</strong> Precise, clinical animations</li>
                </ul>
              </AnimatedCard>
              
              <AnimatedButton 
                persona={persona} 
                onClick={testAnimations}
                className="test-button"
              >
                Test {persona.charAt(0).toUpperCase() + persona.slice(1)} Animations
              </AnimatedButton>
            </div>
          </AnimatedContainer>
        );

      case 'voice':
        return (
          <AnimatedContainer persona={persona} className="feature-content">
            <h3>Voice Recognition Demo</h3>
            <p>Click the button below and try saying commands like:</p>
            <ul>
              <li>"Go to dashboard"</li>
              <li>"Search for agents"</li>
              <li>"Switch to Sophia"</li>
              <li>"Create new project"</li>
            </ul>
            
            <VoiceInput 
              persona={persona} 
              onCommand={handleVoiceCommand}
              className="voice-demo"
            />
          </AnimatedContainer>
        );

      case 'llm':
        return (
          <AnimatedContainer persona={persona} className="feature-content">
            <h3>LLM Integration Demo</h3>
            <p>This feature connects to LLM providers with intelligent routing:</p>
            <div className="llm-info">
              <div className="provider-info">
                <h4>Current Configuration:</h4>
                <ul>
                  <li><strong>Primary:</strong> OpenRouter API</li>
                  <li><strong>Fallback:</strong> Direct provider connections</li>
                  <li><strong>Model for {persona}:</strong> {
                    persona === 'cherry' ? 'GPT-4o' :
                    persona === 'sophia' ? 'Claude-3-Opus' :
                    'GPT-4-Turbo'
                  }</li>
                </ul>
              </div>
              
              <AnimatedButton 
                persona={persona} 
                onClick={() => testFeature('llm')}
                className="test-button"
              >
                Test LLM Integration
              </AnimatedButton>
            </div>
          </AnimatedContainer>
        );

      case 'commands':
        return (
          <AnimatedContainer persona={persona} className="feature-content">
            <h3>Natural Language Commands Demo</h3>
            <p>This feature parses natural language into UI actions:</p>
            
            <div className="commands-info">
              <h4>Supported Command Types:</h4>
              <ul>
                <li><strong>Navigation:</strong> "go to dashboard", "open agents"</li>
                <li><strong>Search:</strong> "search for projects", "find users"</li>
                <li><strong>Creation:</strong> "create new agent", "make project"</li>
                <li><strong>Persona:</strong> "switch to Karen", "talk to Sophia"</li>
              </ul>
              
              <AnimatedButton 
                persona={persona} 
                onClick={() => testFeature('commands')}
                className="test-button"
              >
                Test Command Processing
              </AnimatedButton>
            </div>
          </AnimatedContainer>
        );

      case 'context':
        return (
          <AnimatedContainer persona={persona} className="feature-content">
            <h3>Advanced Context Demo</h3>
            <p>5-tier memory architecture with cross-persona collaboration:</p>
            
            <div className="context-info">
              <h4>Memory Tiers:</h4>
              <ul>
                <li><strong>L0:</strong> CPU Cache (~1ns)</li>
                <li><strong>L1:</strong> Process Memory (~10ns)</li>
                <li><strong>L2:</strong> Redis Cache (~100ns)</li>
                <li><strong>L3:</strong> PostgreSQL (~1ms)</li>
                <li><strong>L4:</strong> Weaviate (~10ms)</li>
              </ul>
              
              <h4>Features:</h4>
              <ul>
                <li>20x token compression</li>
                <li>Cross-domain routing</li>
                <li>Hybrid search capabilities</li>
              </ul>
              
              <AnimatedButton 
                persona={persona} 
                onClick={() => testFeature('context')}
                className="test-button"
              >
                Test Memory System
              </AnimatedButton>
            </div>
          </AnimatedContainer>
        );

      default:
        return null;
    }
  };

  return (
    <motion.div 
      className="feature-demo"
      initial={pageTransition.initial}
      animate={pageTransition.animate}
      exit={pageTransition.exit}
      transition={pageTransition.transition}
    >
      <div className="demo-header">
        <h1>🚀 Orchestra AI Next Phase Features</h1>
        <p>Interactive demonstration of enhanced capabilities</p>
        <div className="persona-indicator">
          Current Persona: <strong>{persona.charAt(0).toUpperCase() + persona.slice(1)}</strong>
        </div>
      </div>

      <div className="demo-layout">
        <div className="feature-sidebar">
          <h3>Features</h3>
          {features.map((feature, index) => (
            <motion.div
              key={feature.id}
              className={`feature-item ${activeFeature === feature.id ? 'active' : ''} ${feature.status}`}
              onClick={() => setActiveFeature(feature.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <div className="feature-info">
                <div className="feature-name">{feature.name}</div>
                <div className="feature-description">{feature.description}</div>
                <div className={`feature-status ${feature.status}`}>
                  {feature.status === 'implemented' ? '✅ Implemented' : 
                   feature.status === 'ready' ? '🔄 Ready' : '⏳ Pending'}
                </div>
              </div>
              {demoData[feature.id]?.tested && (
                <div className="test-indicator">✓</div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="feature-main">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeFeature}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderFeatureContent()}
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="results-sidebar">
          <h3>Test Results</h3>
          <div className="results-container">
            <AnimatePresence>
              {commandResults.map((result) => (
                <motion.div
                  key={result.id}
                  className="result-item"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="result-header">
                    <span className="result-type">{result.type}</span>
                    <span className="result-time">{result.timestamp}</span>
                  </div>
                  <div className="result-content">
                    {JSON.stringify(result.data, null, 2)}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {commandResults.length === 0 && (
              <div className="no-results">
                No test results yet. Try the features above!
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .feature-demo {
          padding: 20px;
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .demo-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .demo-header h1 {
          font-size: 2.5rem;
          margin-bottom: 10px;
        }

        .persona-indicator {
          background: rgba(255, 255, 255, 0.1);
          padding: 10px 20px;
          border-radius: 20px;
          display: inline-block;
          margin-top: 10px;
        }

        .demo-layout {
          display: grid;
          grid-template-columns: 300px 1fr 300px;
          gap: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .feature-sidebar, .results-sidebar {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 15px;
          padding: 20px;
          height: fit-content;
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 15px;
          border-radius: 10px;
          cursor: pointer;
          margin-bottom: 10px;
          transition: all 0.2s ease;
          position: relative;
        }

        .feature-item:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .feature-item.active {
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .feature-icon {
          font-size: 24px;
          min-width: 30px;
        }

        .feature-info {
          flex: 1;
        }

        .feature-name {
          font-weight: 600;
          margin-bottom: 4px;
        }

        .feature-description {
          font-size: 12px;
          opacity: 0.8;
          margin-bottom: 4px;
        }

        .feature-status {
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.1);
        }

        .test-indicator {
          position: absolute;
          top: 5px;
          right: 5px;
          background: #00d2d3;
          color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
        }

        .feature-main {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 15px;
          padding: 30px;
          min-height: 500px;
        }

        .feature-content h3 {
          margin-bottom: 15px;
          font-size: 1.5rem;
        }

        .animation-showcase, .llm-info, .commands-info, .context-info {
          margin-top: 20px;
        }

        .demo-card {
          background: rgba(255, 255, 255, 0.1);
          padding: 20px;
          border-radius: 10px;
          margin-bottom: 20px;
        }

        .test-button {
          margin-top: 15px;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        .voice-demo {
          margin-top: 20px;
          text-align: center;
        }

        .results-container {
          max-height: 400px;
          overflow-y: auto;
        }

        .result-item {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 10px;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 12px;
        }

        .result-type {
          background: #00d2d3;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .result-content {
          font-size: 11px;
          background: rgba(0, 0, 0, 0.2);
          padding: 8px;
          border-radius: 4px;
          white-space: pre-wrap;
          max-height: 100px;
          overflow-y: auto;
        }

        .no-results {
          text-align: center;
          opacity: 0.6;
          padding: 20px;
        }

        @media (max-width: 1200px) {
          .demo-layout {
            grid-template-columns: 1fr;
            gap: 15px;
          }
          
          .feature-sidebar, .results-sidebar {
            order: 2;
          }
          
          .feature-main {
            order: 1;
          }
        }
      `}</style>
    </motion.div>
  );
}; 