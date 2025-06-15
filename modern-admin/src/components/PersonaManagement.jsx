import React, { useState, useEffect } from 'react'
import { 
  User, 
  Settings, 
  Brain, 
  Mic, 
  Search, 
  Palette,
  Save,
  Plus,
  Edit3,
  Trash2,
  Volume2,
  VolumeX,
  AlertCircle,
  CheckCircle,
  Loader
} from 'lucide-react'
import { apiClient } from '../lib/api'

const PersonaManagement = () => {
  const [personas, setPersonas] = useState([])
  const [selectedPersona, setSelectedPersona] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [activeTab, setActiveTab] = useState('identity')

  // Load personas on component mount
  useEffect(() => {
    loadPersonas()
  }, [])

  const loadPersonas = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getPersonas()
      console.log('Personas loaded:', response)
      setPersonas(response)
      if (response.length > 0 && !selectedPersona) {
        setSelectedPersona(response[0])
      }
    } catch (error) {
      console.error('Failed to load personas:', error)
      setMessage({ type: 'error', text: 'Failed to load personas' })
    } finally {
      setIsLoading(false)
    }
  }

  const savePersona = async () => {
    if (!selectedPersona) return

    try {
      setSaving(true)
      const response = await apiClient.updatePersona(selectedPersona.id, {
        name: selectedPersona.name,
        description: selectedPersona.description,
        domain_leanings: selectedPersona.domain_leanings,
        voice_settings: selectedPersona.voice_settings,
        search_preferences: selectedPersona.search_preferences
      })
      
      setMessage({ type: 'success', text: 'Persona updated successfully!' })
      await loadPersonas()
    } catch (error) {
      console.error('Failed to save persona:', error)
      setMessage({ type: 'error', text: 'Failed to save persona' })
    } finally {
      setSaving(false)
    }
  }

  const updatePersonaField = (field, value) => {
    setSelectedPersona(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const updateDomainLeanings = (keywords, preferences) => {
    updatePersonaField('domain_leanings', {
      ...selectedPersona.domain_leanings,
      keywords: keywords.split(',').map(k => k.trim()).filter(k => k),
      preferences: preferences.split(',').map(p => p.trim()).filter(p => p)
    })
  }

  const updateVoiceSettings = (settings) => {
    updatePersonaField('voice_settings', {
      ...selectedPersona.voice_settings,
      ...settings
    })
  }

  const updateSearchPreferences = (preferences) => {
    updatePersonaField('search_preferences', {
      ...selectedPersona.search_preferences,
      ...preferences
    })
  }

  const testVoice = async () => {
    try {
      setMessage({ type: 'info', text: 'Testing voice...' })
      // TODO: Implement voice test API call
      setMessage({ type: 'success', text: 'Voice test completed!' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Voice test failed' })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-blue-400" />
        <span className="ml-2 text-gray-400">Loading personas...</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-blue-400" />
            <h1 className="text-xl font-semibold">Persona Management</h1>
          </div>
          
          <div className="flex items-center space-x-3">
            {message.text && (
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-lg text-sm ${
                message.type === 'success' ? 'bg-green-500/20 text-green-400' :
                message.type === 'error' ? 'bg-red-500/20 text-red-400' :
                'bg-blue-500/20 text-blue-400'
              }`}>
                {message.type === 'success' && <CheckCircle className="w-4 h-4" />}
                {message.type === 'error' && <AlertCircle className="w-4 h-4" />}
                <span>{message.text}</span>
              </div>
            )}
            
            <button
              onClick={savePersona}
              disabled={isSaving || !selectedPersona}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              {isSaving ? <Loader className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              <span>{isSaving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Persona List Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium">Personas</h2>
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          <div className="space-y-2">
            {personas.map((persona) => (
              <div
                key={persona.id}
                onClick={() => setSelectedPersona(persona)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedPersona?.id === persona.id
                    ? 'bg-blue-600/20 border border-blue-500/30'
                    : 'bg-gray-700/50 hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                      persona.name === 'Cherry' ? 'bg-red-500/20 text-red-400' :
                      persona.name === 'Sophia' ? 'bg-blue-500/20 text-blue-400' :
                      persona.name === 'Karen' ? 'bg-green-500/20 text-green-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {persona.name[0]}
                    </div>
                    <div>
                      <h3 className="font-medium">{persona.name}</h3>
                      <p className="text-sm text-gray-400 capitalize">{persona.persona_type}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <button className="p-1 text-gray-400 hover:text-white transition-colors">
                      <Edit3 className="w-3 h-3" />
                    </button>
                    <button className="p-1 text-gray-400 hover:text-red-400 transition-colors">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                
                <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                  {persona.description || 'No description'}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {selectedPersona ? (
            <div>
              {/* Persona Header */}
              <div className="flex items-center space-x-4 mb-6">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold ${
                  selectedPersona.name === 'Cherry' ? 'bg-red-500/20 text-red-400' :
                  selectedPersona.name === 'Sophia' ? 'bg-blue-500/20 text-blue-400' :
                  selectedPersona.name === 'Karen' ? 'bg-green-500/20 text-green-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {selectedPersona.name[0]}
                </div>
                
                <div>
                  <input
                    type="text"
                    value={selectedPersona.name}
                    onChange={(e) => updatePersonaField('name', e.target.value)}
                    className="text-2xl font-bold bg-transparent border-none outline-none text-white"
                  />
                  <p className="text-gray-400 capitalize">{selectedPersona.persona_type}</p>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex space-x-1 mb-6 bg-gray-800 p-1 rounded-lg">
                {[
                  { id: 'identity', label: 'Identity', icon: User },
                  { id: 'domain', label: 'Domain Leanings', icon: Brain },
                  { id: 'voice', label: 'Voice Settings', icon: Mic },
                  { id: 'search', label: 'Search Preferences', icon: Search },
                  { id: 'creative', label: 'Creative Tools', icon: Palette }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="bg-gray-800 rounded-lg p-6">
                {activeTab === 'identity' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Description
                      </label>
                      <textarea
                        value={selectedPersona.description || ''}
                        onChange={(e) => updatePersonaField('description', e.target.value)}
                        rows={4}
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Describe this persona's role and personality..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Persona Type
                      </label>
                      <select
                        value={selectedPersona.persona_type}
                        onChange={(e) => updatePersonaField('persona_type', e.target.value)}
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="assistant">Assistant</option>
                        <option value="analyst">Analyst</option>
                        <option value="manager">Manager</option>
                        <option value="creative">Creative</option>
                        <option value="specialist">Specialist</option>
                      </select>
                    </div>
                  </div>
                )}

                {activeTab === 'domain' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Domain Keywords
                      </label>
                      <input
                        type="text"
                        value={selectedPersona.domain_leanings?.keywords?.join(', ') || ''}
                        onChange={(e) => updateDomainLeanings(
                          e.target.value,
                          selectedPersona.domain_leanings?.preferences?.join(', ') || ''
                        )}
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="business, property rental, technology, etc."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Comma-separated keywords that influence search and response weighting
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Preferences
                      </label>
                      <input
                        type="text"
                        value={selectedPersona.domain_leanings?.preferences?.join(', ') || ''}
                        onChange={(e) => updateDomainLeanings(
                          selectedPersona.domain_leanings?.keywords?.join(', ') || '',
                          e.target.value
                        )}
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="analytical approach, business focus, data driven, etc."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Behavioral preferences that subtly influence responses
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'voice' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Voice Model
                        </label>
                        <select
                          value={selectedPersona.voice_settings?.voice_id || ''}
                          onChange={(e) => updateVoiceSettings({ voice_id: e.target.value })}
                          className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select Voice</option>
                          <option value="cherry_voice">Cherry Voice</option>
                          <option value="sophia_voice">Sophia Voice</option>
                          <option value="karen_voice">Karen Voice</option>
                        </select>
                      </div>
                      
                      <div className="flex items-end">
                        <button
                          onClick={testVoice}
                          className="flex items-center space-x-2 px-4 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                        >
                          <Volume2 className="w-4 h-4" />
                          <span>Test Voice</span>
                        </button>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Stability: {selectedPersona.voice_settings?.stability || 0.75}
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={selectedPersona.voice_settings?.stability || 0.75}
                          onChange={(e) => updateVoiceSettings({ stability: parseFloat(e.target.value) })}
                          className="w-full"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Similarity: {selectedPersona.voice_settings?.similarity_boost || 0.75}
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={selectedPersona.voice_settings?.similarity_boost || 0.75}
                          onChange={(e) => updateVoiceSettings({ similarity_boost: parseFloat(e.target.value) })}
                          className="w-full"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Style: {selectedPersona.voice_settings?.style || 0.5}
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={selectedPersona.voice_settings?.style || 0.5}
                          onChange={(e) => updateVoiceSettings({ style: parseFloat(e.target.value) })}
                          className="w-full"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'search' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Default Search Mode
                      </label>
                      <select
                        value={selectedPersona.search_preferences?.default_mode || 'normal'}
                        onChange={(e) => updateSearchPreferences({ default_mode: e.target.value })}
                        className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="normal">Normal</option>
                        <option value="deep">Deep Search</option>
                        <option value="super_deep">Super Deep Search</option>
                      </select>
                    </div>
                    
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedPersona.search_preferences?.enable_uncensored || false}
                          onChange={(e) => updateSearchPreferences({ enable_uncensored: e.target.checked })}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-300">Enable Uncensored Mode</span>
                      </label>
                      
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedPersona.search_preferences?.creative_priority || false}
                          onChange={(e) => updateSearchPreferences({ creative_priority: e.target.checked })}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-300">Prioritize Creative Content</span>
                      </label>
                      
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedPersona.search_preferences?.business_priority || false}
                          onChange={(e) => updateSearchPreferences({ business_priority: e.target.checked })}
                          className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-300">Prioritize Business Content</span>
                      </label>
                    </div>
                  </div>
                )}

                {activeTab === 'creative' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-lg font-medium mb-3">Creative Functions</h3>
                        <div className="space-y-2">
                          {selectedPersona.name === 'Cherry' && (
                            <>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Create Image</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Edit Image</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Create Video</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Create Song</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Write Story</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                            </>
                          )}
                          
                          {(selectedPersona.name === 'Sophia' || selectedPersona.name === 'Karen') && (
                            <>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Create Presentation</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Marketing Content</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                                <span>Internal Communication</span>
                                <span className="text-green-400 text-sm">Enabled</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-medium mb-3">API Access</h3>
                        <div className="space-y-2">
                          {Object.entries(selectedPersona.api_access_config || {}).map(([api, enabled]) => (
                            <div key={api} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                              <span className="capitalize">{api.replace('_', ' ')}</span>
                              <span className={`text-sm ${enabled ? 'text-green-400' : 'text-red-400'}`}>
                                {enabled ? 'Enabled' : 'Disabled'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Brain className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-gray-400 mb-2">No Persona Selected</h3>
                <p className="text-gray-500">Select a persona from the sidebar to manage its settings</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PersonaManagement

