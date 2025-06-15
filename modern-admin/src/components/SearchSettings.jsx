import { useState, useEffect } from 'react'
import { 
  Settings, 
  Search, 
  Sliders, 
  Database, 
  Globe, 
  Save,
  Plus,
  X,
  ChevronRight,
  Shield,
  Sparkles,
  Building,
  Heart
} from 'lucide-react'

export default function SearchSettings({ activePersona }) {
  const [settings, setSettings] = useState({
    blendRatios: {
      default: { database: 50, web: 50 },
      cherry: { database: 40, web: 60 },
      sophia: { database: 60, web: 40 },
      karen: { database: 70, web: 30 }
    },
    searchModes: {
      cherry: {
        default: 'normal',
        allowUncensored: true,
        preferences: ['creative', 'personal', 'entertainment'],
        interests: []
      },
      sophia: {
        default: 'deep',
        businessFocus: true,
        payReadyClients: [],
        payReadyCompetitors: [],
        industryKeywords: ['apartment rental', 'property technology', 'debt collection', 'payment systems']
      },
      karen: {
        default: 'deep',
        clinicalFocus: true,
        trackedTrials: [],
        specialties: ['clinical trials', 'pharmaceutical approvals', 'healthcare operations'],
        regulatoryAlerts: true
      }
    }
  })

  const [showWizard, setShowWizard] = useState(false)
  const [unsavedChanges, setUnsavedChanges] = useState(false)

  // Save settings to backend
  const saveSettings = async () => {
    try {
      // API call would go here
      console.log('Saving settings:', settings)
      setUnsavedChanges(false)
      // Show success toast
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  const updateBlendRatio = (persona, type, value) => {
    setSettings(prev => ({
      ...prev,
      blendRatios: {
        ...prev.blendRatios,
        [persona]: {
          ...prev.blendRatios[persona],
          [type]: value,
          [type === 'database' ? 'web' : 'database']: 100 - value
        }
      }
    }))
    setUnsavedChanges(true)
  }

  const addDomainItem = (persona, field, item) => {
    if (!item.trim()) return
    
    setSettings(prev => ({
      ...prev,
      searchModes: {
        ...prev.searchModes,
        [persona]: {
          ...prev.searchModes[persona],
          [field]: [...(prev.searchModes[persona][field] || []), item]
        }
      }
    }))
    setUnsavedChanges(true)
  }

  const removeDomainItem = (persona, field, index) => {
    setSettings(prev => ({
      ...prev,
      searchModes: {
        ...prev.searchModes,
        [persona]: {
          ...prev.searchModes[persona],
          [field]: prev.searchModes[persona][field].filter((_, i) => i !== index)
        }
      }
    }))
    setUnsavedChanges(true)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Settings className="w-8 h-8 text-blue-500" />
              Search Configuration
            </h1>
            <p className="text-gray-400 mt-2">
              Customize search behavior and domain preferences for each persona
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {unsavedChanges && (
              <span className="text-yellow-500 text-sm">Unsaved changes</span>
            )}
            <button
              onClick={() => setShowWizard(true)}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Configuration Wizard
            </button>
            <button
              onClick={saveSettings}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>

        {/* Blend Ratio Settings */}
        <section className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            Search Blend Ratios
          </h2>
          
          <p className="text-gray-400 text-sm mb-6">
            Adjust how search results are weighted between internal database and web sources
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {['default', 'cherry', 'sophia', 'karen'].map((persona) => (
              <div key={persona} className="space-y-3">
                <h3 className="font-medium capitalize">
                  {persona === 'default' ? 'Default Settings' : `${persona} Settings`}
                </h3>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-green-400" />
                      Database
                    </span>
                    <span>{settings.blendRatios[persona].database}%</span>
                  </div>
                  
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.blendRatios[persona].database}
                    onChange={(e) => updateBlendRatio(persona, 'database', parseInt(e.target.value))}
                    className="w-full"
                  />
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-blue-400" />
                      Web Search
                    </span>
                    <span>{settings.blendRatios[persona].web}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Persona-Specific Settings */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cherry Settings */}
          <section className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-400" />
              Cherry (Personal)
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Default Search Mode
                </label>
                <select 
                  value={settings.searchModes.cherry.default}
                  onChange={(e) => {
                    setSettings(prev => ({
                      ...prev,
                      searchModes: {
                        ...prev.searchModes,
                        cherry: { ...prev.searchModes.cherry, default: e.target.value }
                      }
                    }))
                    setUnsavedChanges(true)
                  }}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
                >
                  <option value="normal">Normal</option>
                  <option value="deep">Deep</option>
                  <option value="deeper">Deeper</option>
                  <option value="uncensored">Uncensored</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.searchModes.cherry.allowUncensored}
                    onChange={(e) => {
                      setSettings(prev => ({
                        ...prev,
                        searchModes: {
                          ...prev.searchModes,
                          cherry: { ...prev.searchModes.cherry, allowUncensored: e.target.checked }
                        }
                      }))
                      setUnsavedChanges(true)
                    }}
                    className="rounded border-gray-600 bg-gray-700 text-blue-600"
                  />
                  <Shield className="w-4 h-4 text-red-400" />
                  <span className="text-sm">Allow Uncensored Mode</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Interests & Preferences
                </label>
                <div className="space-y-2">
                  {settings.searchModes.cherry.interests.map((interest, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="flex-1 text-sm bg-gray-700 px-3 py-1 rounded">
                        {interest}
                      </span>
                      <button
                        onClick={() => removeDomainItem('cherry', 'interests', idx)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Add interest..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addDomainItem('cherry', 'interests', e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Sophia Settings */}
          <section className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Building className="w-5 h-5 text-blue-400" />
              Sophia (Pay Ready)
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Pay Ready Clients
                </label>
                <div className="space-y-2">
                  {settings.searchModes.sophia.payReadyClients.map((client, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="flex-1 text-sm bg-gray-700 px-3 py-1 rounded">
                        {client}
                      </span>
                      <button
                        onClick={() => removeDomainItem('sophia', 'payReadyClients', idx)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Add client..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addDomainItem('sophia', 'payReadyClients', e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Competitors
                </label>
                <div className="space-y-2">
                  {settings.searchModes.sophia.payReadyCompetitors.map((competitor, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="flex-1 text-sm bg-gray-700 px-3 py-1 rounded">
                        {competitor}
                      </span>
                      <button
                        onClick={() => removeDomainItem('sophia', 'payReadyCompetitors', idx)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Add competitor..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addDomainItem('sophia', 'payReadyCompetitors', e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Karen Settings */}
          <section className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 text-green-400" />
              Karen (ParagonRX)
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tracked Clinical Trials
                </label>
                <div className="space-y-2">
                  {settings.searchModes.karen.trackedTrials.map((trial, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="flex-1 text-sm bg-gray-700 px-3 py-1 rounded">
                        {trial}
                      </span>
                      <button
                        onClick={() => removeDomainItem('karen', 'trackedTrials', idx)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <input
                    type="text"
                    placeholder="Add trial ID or name..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addDomainItem('karen', 'trackedTrials', e.target.value)
                        e.target.value = ''
                      }
                    }}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.searchModes.karen.regulatoryAlerts}
                    onChange={(e) => {
                      setSettings(prev => ({
                        ...prev,
                        searchModes: {
                          ...prev.searchModes,
                          karen: { ...prev.searchModes.karen, regulatoryAlerts: e.target.checked }
                        }
                      }))
                      setUnsavedChanges(true)
                    }}
                    className="rounded border-gray-600 bg-gray-700 text-blue-600"
                  />
                  <span className="text-sm">Enable Regulatory Alerts</span>
                </label>
              </div>
            </div>
          </section>
        </div>

        {/* Configuration Wizard Modal */}
        {showWizard && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-6">Search Configuration Wizard</h2>
              <p className="text-gray-400 mb-6">
                Let's set up your search preferences step by step...
              </p>
              
              {/* Wizard content would go here */}
              
              <div className="flex justify-end gap-4 mt-8">
                <button
                  onClick={() => setShowWizard(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setShowWizard(false)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Complete Setup
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 