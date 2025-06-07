import React, { useState } from 'react';
import { Search, Brain, Zap, Shield, BarChart3, FileText, TrendingUp, Clock, Target, Database, Settings, Play, Pause, Eye, ChevronRight } from 'lucide-react';

const SearchOrchestratorPage = () => {
  const [selectedMode, setSelectedMode] = useState('normal');
  const [activeTab, setActiveTab] = useState('overview');

  const searchModes = [
    {
      id: 'normal',
      name: 'Normal Search',
      icon: Search,
      description: 'Standard semantic search for quick results',
      status: 'active',
      color: '#3b82f6',
      avgResponseTime: '0.8s',
      accuracy: 87,
      costPerQuery: '$0.002',
      queriesLast24h: 2847,
      successRate: 94.2,
      features: ['Semantic Matching', 'Fast Response', 'Basic Ranking'],
      config: {
        vectorSearch: true,
        rerankingEnabled: false,
        maxResults: 10,
        threshold: 0.7
      }
    },
    {
      id: 'deep',
      name: 'Deep Search',
      icon: Brain,
      description: 'Enhanced search with re-ranking and context analysis',
      status: 'active',
      color: '#8b5cf6',
      avgResponseTime: '2.1s',
      accuracy: 92,
      costPerQuery: '$0.008',
      queriesLast24h: 1234,
      successRate: 96.8,
      features: ['Vector Search', 'Re-ranking', 'Context Analysis', 'Multiple Sources'],
      config: {
        vectorSearch: true,
        rerankingEnabled: true,
        maxResults: 15,
        threshold: 0.6
      }
    },
    {
      id: 'super-deep',
      name: 'Super Deep Search',
      icon: Zap,
      description: 'Multi-stage search with advanced reasoning',
      status: 'active',
      color: '#f59e0b',
      avgResponseTime: '4.7s',
      accuracy: 96,
      costPerQuery: '$0.025',
      queriesLast24h: 456,
      successRate: 98.1,
      features: ['Multi-Vector Search', 'Advanced Re-ranking', 'Cross-Reference', 'Deep Analysis'],
      config: {
        vectorSearch: true,
        rerankingEnabled: true,
        maxResults: 25,
        threshold: 0.5,
        multiStage: true
      }
    },
    {
      id: 'creative',
      name: 'Creative Search',
      icon: Brain,
      description: 'Exploratory search for innovative connections',
      status: 'active',
      color: '#ec4899',
      avgResponseTime: '3.2s',
      accuracy: 89,
      costPerQuery: '$0.015',
      queriesLast24h: 789,
      successRate: 91.5,
      features: ['Associative Matching', 'Divergent Thinking', 'Pattern Discovery'],
      config: {
        vectorSearch: true,
        creativityBoost: true,
        explorationWeight: 0.8,
        maxResults: 20
      }
    },
    {
      id: 'private',
      name: 'Private Search',
      icon: Shield,
      description: 'Secure search with data isolation',
      status: 'active',
      color: '#10b981',
      avgResponseTime: '1.4s',
      accuracy: 85,
      costPerQuery: '$0.005',
      queriesLast24h: 567,
      successRate: 93.7,
      features: ['Data Isolation', 'Encrypted Queries', 'Local Processing'],
      config: {
        encryption: true,
        localProcessing: true,
        dataIsolation: true,
        maxResults: 12
      }
    },
    {
      id: 'analytical',
      name: 'Analytical Search',
      icon: BarChart3,
      description: 'Data-driven search with statistical insights',
      status: 'active',
      color: '#06b6d4',
      avgResponseTime: '2.8s',
      accuracy: 94,
      costPerQuery: '$0.012',
      queriesLast24h: 1023,
      successRate: 97.3,
      features: ['Statistical Analysis', 'Trend Detection', 'Data Correlation'],
      config: {
        statisticalAnalysis: true,
        trendDetection: true,
        correlationAnalysis: true,
        maxResults: 18
      }
    },
    {
      id: 'research',
      name: 'Research Search',
      icon: FileText,
      description: 'Comprehensive search for academic and technical queries',
      status: 'active',
      color: '#dc2626',
      avgResponseTime: '5.9s',
      accuracy: 98,
      costPerQuery: '$0.035',
      queriesLast24h: 234,
      successRate: 99.2,
      features: ['Citation Tracking', 'Source Verification', 'Comprehensive Analysis'],
      config: {
        citationTracking: true,
        sourceVerification: true,
        comprehensiveAnalysis: true,
        maxResults: 30,
        academicBoost: true
      }
    }
  ];

  const recentQueries = [
    {
      id: '1',
      query: 'Q2 revenue analysis financial trends',
      mode: 'analytical',
      responseTime: '2.3s',
      accuracy: 94,
      results: 15,
      timestamp: '2 min ago',
      status: 'completed'
    },
    {
      id: '2',
      query: 'Customer satisfaction patterns and insights',
      mode: 'deep',
      responseTime: '1.8s',
      accuracy: 96,
      results: 12,
      timestamp: '5 min ago',
      status: 'completed'
    },
    {
      id: '3',
      query: 'Innovative marketing strategies for Q3 launch',
      mode: 'creative',
      responseTime: '3.1s',
      accuracy: 89,
      results: 18,
      timestamp: '8 min ago',
      status: 'completed'
    },
    {
      id: '4',
      query: 'Clinical trial data validation protocols',
      mode: 'research',
      responseTime: '5.7s',
      accuracy: 98,
      results: 24,
      timestamp: '12 min ago',
      status: 'completed'
    },
    {
      id: '5',
      query: 'Secure document processing workflow',
      mode: 'private',
      responseTime: '1.2s',
      accuracy: 91,
      results: 8,
      timestamp: '15 min ago',
      status: 'completed'
    }
  ];

  const getCurrentMode = () => {
    return searchModes.find(mode => mode.id === selectedMode) || searchModes[0];
  };

  const currentMode = getCurrentMode();

  const overallStats = {
    totalQueries: searchModes.reduce((sum, mode) => sum + mode.queriesLast24h, 0),
    avgAccuracy: Math.round(searchModes.reduce((sum, mode) => sum + mode.accuracy, 0) / searchModes.length),
    avgResponseTime: '2.4s',
    totalCost: '$127.34'
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a1a1a 100%)',
      color: '#ffffff',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.4)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(220, 38, 127, 0.2)',
        padding: '24px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div>
            <h1 style={{
              fontSize: '32px',
              fontWeight: '700',
              margin: '0 0 8px 0',
              background: 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Search Orchestrator
            </h1>
            <p style={{
              color: '#888',
              fontSize: '16px',
              margin: '0'
            }}>
              Manage and monitor your 7-mode intelligent search system
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button style={{
              background: 'rgba(220, 38, 127, 0.1)',
              border: '1px solid rgba(220, 38, 127, 0.3)',
              borderRadius: '8px',
              padding: '8px 16px',
              color: '#dc267f',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}>
              <Settings className="w-4 h-4" />
              Global Settings
            </button>
            
            <button style={{
              background: 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              fontWeight: '500'
            }}>
              <Play className="w-4 h-4" />
              Run Test Query
            </button>
          </div>
        </div>
      </div>

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '24px'
      }}>
        {/* Overall Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '32px'
        }}>
          {[
            { label: 'Total Queries (24h)', value: overallStats.totalQueries.toLocaleString(), icon: Search, color: '#3b82f6' },
            { label: 'Avg Accuracy', value: `${overallStats.avgAccuracy}%`, icon: Target, color: '#10b981' },
            { label: 'Avg Response Time', value: overallStats.avgResponseTime, icon: Clock, color: '#f59e0b' },
            { label: 'Total Cost (24h)', value: overallStats.totalCost, icon: TrendingUp, color: '#dc267f' }
          ].map((stat, index) => (
            <div key={index} style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              padding: '24px',
              textAlign: 'center'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '12px'
              }}>
                <div style={{
                  background: `${stat.color}20`,
                  borderRadius: '12px',
                  padding: '12px',
                  display: 'inline-flex'
                }}>
                  <stat.icon style={{ width: '24px', height: '24px', color: stat.color }} />
                </div>
              </div>
              <div style={{
                fontSize: '32px',
                fontWeight: '700',
                color: stat.color,
                marginBottom: '4px'
              }}>
                {stat.value}
              </div>
              <div style={{
                color: '#888',
                fontSize: '14px'
              }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Search Modes Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '20px',
          marginBottom: '32px'
        }}>
          {searchModes.map(mode => (
            <div 
              key={mode.id}
              onClick={() => setSelectedMode(mode.id)}
              style={{
                background: selectedMode === mode.id 
                  ? 'rgba(220, 38, 127, 0.1)' 
                  : 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(20px)',
                border: selectedMode === mode.id 
                  ? '1px solid rgba(220, 38, 127, 0.3)' 
                  : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '16px',
                padding: '20px',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              {/* Mode Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '16px'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <div style={{
                      background: `${mode.color}20`,
                      borderRadius: '10px',
                      padding: '8px',
                      display: 'flex'
                    }}>
                      <mode.icon style={{ width: '20px', height: '20px', color: mode.color }} />
                    </div>
                    <h3 style={{
                      fontSize: '18px',
                      fontWeight: '600',
                      margin: '0',
                      color: '#ffffff'
                    }}>
                      {mode.name}
                    </h3>
                  </div>
                  <p style={{
                    color: '#888',
                    fontSize: '13px',
                    margin: '0',
                    lineHeight: '1.4'
                  }}>
                    {mode.description}
                  </p>
                </div>
                
                <div style={{
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '6px',
                  padding: '4px 8px',
                  fontSize: '11px',
                  color: '#10b981',
                  fontWeight: '500',
                  textTransform: 'uppercase'
                }}>
                  {mode.status}
                </div>
              </div>

              {/* Metrics */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px',
                marginBottom: '16px'
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: mode.color
                  }}>
                    {mode.avgResponseTime}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#888'
                  }}>
                    Response Time
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: mode.color
                  }}>
                    {mode.accuracy}%
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#888'
                  }}>
                    Accuracy
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: mode.color
                  }}>
                    {mode.queriesLast24h.toLocaleString()}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#888'
                  }}>
                    Queries (24h)
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: mode.color
                  }}>
                    {mode.costPerQuery}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#888'
                  }}>
                    Cost/Query
                  </div>
                </div>
              </div>

              {/* Features */}
              <div>
                <div style={{
                  fontSize: '12px',
                  color: '#888',
                  marginBottom: '8px'
                }}>
                  Key Features
                </div>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '4px'
                }}>
                  {mode.features.slice(0, 2).map((feature, index) => (
                    <span key={index} style={{
                      background: `${mode.color}15`,
                      border: `1px solid ${mode.color}30`,
                      borderRadius: '6px',
                      padding: '2px 6px',
                      fontSize: '10px',
                      color: mode.color
                    }}>
                      {feature}
                    </span>
                  ))}
                  {mode.features.length > 2 && (
                    <span style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '6px',
                      padding: '2px 6px',
                      fontSize: '10px',
                      color: '#888'
                    }}>
                      +{mode.features.length - 2} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Mode Details */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '32px'
        }}>
          {/* Mode Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              background: `${currentMode.color}20`,
              borderRadius: '16px',
              padding: '12px',
              display: 'flex'
            }}>
              <currentMode.icon style={{ width: '32px', height: '32px', color: currentMode.color }} />
            </div>
            <div>
              <h2 style={{
                fontSize: '24px',
                fontWeight: '600',
                margin: '0 0 4px 0',
                color: '#ffffff'
              }}>
                {currentMode.name} Details
              </h2>
              <p style={{
                color: '#888',
                fontSize: '14px',
                margin: '0'
              }}>
                {currentMode.description}
              </p>
            </div>
          </div>

          {/* Tabs */}
          <div style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '24px',
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '12px',
            padding: '8px'
          }}>
            {[
              { id: 'overview', label: 'Overview', icon: Eye },
              { id: 'config', label: 'Configuration', icon: Settings },
              { id: 'queries', label: 'Recent Queries', icon: FileText }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: activeTab === tab.id 
                    ? `linear-gradient(135deg, ${currentMode.color} 0%, ${currentMode.color}80 100%)`
                    : 'transparent',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 20px',
                  color: activeTab === tab.id ? '#ffffff' : '#888',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px'
            }}>
              {[
                { label: 'Queries Today', value: currentMode.queriesLast24h.toLocaleString(), change: '+12%' },
                { label: 'Success Rate', value: `${currentMode.successRate}%`, change: '+2.1%' },
                { label: 'Avg Response', value: currentMode.avgResponseTime, change: '-5%' },
                { label: 'Cost Efficiency', value: currentMode.costPerQuery, change: '-8%' }
              ].map((metric, index) => (
                <div key={index} style={{
                  background: 'rgba(0, 0, 0, 0.2)',
                  borderRadius: '12px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    color: currentMode.color,
                    marginBottom: '4px'
                  }}>
                    {metric.value}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#888',
                    marginBottom: '8px'
                  }}>
                    {metric.label}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: metric.change.startsWith('+') ? '#10b981' : '#ef4444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px'
                  }}>
                    <TrendingUp className="w-3 h-3" />
                    {metric.change}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'config' && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '20px'
            }}>
              {Object.entries(currentMode.config).map(([key, value]) => (
                <div key={key} style={{
                  background: 'rgba(0, 0, 0, 0.2)',
                  borderRadius: '12px',
                  padding: '20px'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      color: '#ffffff',
                      textTransform: 'capitalize'
                    }}>
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </span>
                    <span style={{
                      fontSize: '14px',
                      color: currentMode.color,
                      fontWeight: '500'
                    }}>
                      {typeof value === 'boolean' 
                        ? (value ? 'Enabled' : 'Disabled')
                        : value.toString()}
                    </span>
                  </div>
                  <div style={{
                    height: '4px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '2px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      height: '100%',
                      width: typeof value === 'boolean' 
                        ? (value ? '100%' : '0%')
                        : `${Math.min(100, parseFloat(value.toString()) * 100)}%`,
                      background: currentMode.color,
                      borderRadius: '2px'
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'queries' && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              {recentQueries
                .filter(query => query.mode === selectedMode)
                .map(query => (
                  <div key={query.id} style={{
                    background: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '12px',
                    padding: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px'
                  }}>
                    <div style={{
                      background: `${currentMode.color}20`,
                      borderRadius: '10px',
                      padding: '10px',
                      display: 'flex'
                    }}>
                      <Search style={{ width: '20px', height: '20px', color: currentMode.color }} />
                    </div>
                    
                    <div style={{ flex: 1 }}>
                      <h4 style={{
                        fontSize: '14px',
                        fontWeight: '500',
                        margin: '0 0 4px 0',
                        color: '#ffffff'
                      }}>
                        "{query.query}"
                      </h4>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        fontSize: '12px',
                        color: '#888'
                      }}>
                        <span>{query.timestamp}</span>
                        <span>•</span>
                        <span>{query.responseTime}</span>
                        <span>•</span>
                        <span>{query.results} results</span>
                        <span>•</span>
                        <span style={{ color: currentMode.color }}>{query.accuracy}% accuracy</span>
                      </div>
                    </div>

                    <button style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '8px 12px',
                      color: '#888',
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      View Results
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchOrchestratorPage; 