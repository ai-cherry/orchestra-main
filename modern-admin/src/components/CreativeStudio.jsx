import React, { useState, useEffect } from 'react'
import { 
  FileText, 
  Image, 
  Video, 
  Music, 
  Presentation,
  Download,
  Eye,
  Trash2,
  Plus,
  Sparkles,
  Palette,
  Mic,
  Camera,
  PenTool
} from 'lucide-react'
import apiClient from '../lib/api'

const CreativeStudio = () => {
  const [activeTab, setActiveTab] = useState('documents')
  const [creativeGallery, setCreativeGallery] = useState({
    documents: [],
    images: [],
    videos: [],
    audio: [],
    presentations: []
  })
  const [templates, setTemplates] = useState({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createType, setCreateType] = useState('')

  // Load creative gallery and templates
  useEffect(() => {
    loadCreativeGallery()
    loadTemplates()
  }, [])

  const loadCreativeGallery = async () => {
    try {
      const gallery = await apiClient.getCreativeGallery()
      setCreativeGallery(gallery)
    } catch (error) {
      console.error('Failed to load creative gallery:', error)
    }
  }

  const loadTemplates = async () => {
    try {
      const templatesData = await apiClient.getCreativeTemplates()
      setTemplates(templatesData)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const tabs = [
    { id: 'documents', name: 'Documents', icon: FileText, color: 'text-blue-500' },
    { id: 'images', name: 'Images', icon: Image, color: 'text-green-500' },
    { id: 'videos', name: 'Videos', icon: Video, color: 'text-purple-500' },
    { id: 'audio', name: 'Audio', icon: Music, color: 'text-orange-500' },
    { id: 'presentations', name: 'Presentations', icon: Presentation, color: 'text-pink-500' }
  ]

  const creationOptions = {
    documents: [
      { id: 'business_report', name: 'Business Report', description: 'Comprehensive analysis and insights' },
      { id: 'project_proposal', name: 'Project Proposal', description: 'Professional project proposal' },
      { id: 'executive_memo', name: 'Executive Memo', description: 'Executive communication' },
      { id: 'marketing_brief', name: 'Marketing Brief', description: 'Marketing campaign brief' }
    ],
    images: [
      { id: 'professional', name: 'Professional Graphics', description: 'Business-focused imagery' },
      { id: 'creative', name: 'Creative Visuals', description: 'Artistic and innovative designs' },
      { id: 'infographic', name: 'Infographics', description: 'Data visualization graphics' },
      { id: 'social_media', name: 'Social Media', description: 'Social media optimized graphics' }
    ],
    videos: [
      { id: 'explainer', name: 'Explainer Video', description: 'Product and concept explanations' },
      { id: 'marketing', name: 'Marketing Video', description: 'Promotional content' },
      { id: 'educational', name: 'Educational Content', description: 'Training and tutorials' },
      { id: 'testimonial', name: 'Testimonial', description: 'Customer testimonials' }
    ],
    audio: [
      { id: 'voiceover', name: 'Voiceover', description: 'Professional narration' },
      { id: 'background_music', name: 'Background Music', description: 'Ambient music tracks' },
      { id: 'sound_effects', name: 'Sound Effects', description: 'Custom sound effects' },
      { id: 'podcast', name: 'Podcast Audio', description: 'Podcast-style content' }
    ],
    presentations: [
      { id: 'business', name: 'Business Presentation', description: 'Professional business slides' },
      { id: 'sales', name: 'Sales Pitch', description: 'Sales presentation template' },
      { id: 'training', name: 'Training Slides', description: 'Educational presentation' },
      { id: 'creative', name: 'Creative Presentation', description: 'Engaging visual slides' }
    ]
  }

  const handleCreateContent = (type) => {
    setCreateType(type)
    setShowCreateModal(true)
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center">
              <Sparkles className="w-8 h-8 mr-3 text-purple-400" />
              Creative Studio
            </h1>
            <p className="text-gray-400 mt-2">
              Generate professional content with AI-powered creativity
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-gray-400">Total Assets</div>
              <div className="text-2xl font-bold text-white">
                {Object.values(creativeGallery).reduce((total, items) => total + items.length, 0)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="flex space-x-8 px-6">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? tab.color : ''}`} />
                <span className="font-medium">{tab.name}</span>
                <span className="bg-gray-700 text-xs px-2 py-1 rounded-full">
                  {creativeGallery[tab.id]?.length || 0}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className="p-6">
        {/* Create New Content Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">
              Create New {tabs.find(t => t.id === activeTab)?.name}
            </h2>
            <button
              onClick={() => handleCreateContent(activeTab)}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create New</span>
            </button>
          </div>

          {/* Creation Options Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {creationOptions[activeTab]?.map((option) => (
              <div
                key={option.id}
                onClick={() => handleCreateContent(activeTab)}
                className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-blue-500 cursor-pointer transition-colors group"
              >
                <div className="flex items-center space-x-3 mb-2">
                  {activeTab === 'documents' && <FileText className="w-6 h-6 text-blue-400" />}
                  {activeTab === 'images' && <Image className="w-6 h-6 text-green-400" />}
                  {activeTab === 'videos' && <Video className="w-6 h-6 text-purple-400" />}
                  {activeTab === 'audio' && <Music className="w-6 h-6 text-orange-400" />}
                  {activeTab === 'presentations' && <Presentation className="w-6 h-6 text-pink-400" />}
                  <h3 className="font-medium text-white group-hover:text-blue-400 transition-colors">
                    {option.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-400">{option.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Gallery Section */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-4">
            Your {tabs.find(t => t.id === activeTab)?.name} Gallery
          </h2>

          {creativeGallery[activeTab]?.length === 0 ? (
            <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
              <div className="flex justify-center mb-4">
                {activeTab === 'documents' && <FileText className="w-16 h-16 text-gray-600" />}
                {activeTab === 'images' && <Image className="w-16 h-16 text-gray-600" />}
                {activeTab === 'videos' && <Video className="w-16 h-16 text-gray-600" />}
                {activeTab === 'audio' && <Music className="w-16 h-16 text-gray-600" />}
                {activeTab === 'presentations' && <Presentation className="w-16 h-16 text-gray-600" />}
              </div>
              <h3 className="text-lg font-medium text-gray-400 mb-2">
                No {activeTab} created yet
              </h3>
              <p className="text-gray-500 mb-4">
                Start creating amazing content with AI assistance
              </p>
              <button
                onClick={() => handleCreateContent(activeTab)}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
              >
                Create Your First {tabs.find(t => t.id === activeTab)?.name.slice(0, -1)}
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {creativeGallery[activeTab]?.map((item) => (
                <div
                  key={item.id}
                  className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden hover:border-blue-500 transition-colors group"
                >
                  {/* Preview Area */}
                  <div className="aspect-video bg-gray-700 flex items-center justify-center">
                    {activeTab === 'documents' && <FileText className="w-12 h-12 text-blue-400" />}
                    {activeTab === 'images' && <Image className="w-12 h-12 text-green-400" />}
                    {activeTab === 'videos' && <Video className="w-12 h-12 text-purple-400" />}
                    {activeTab === 'audio' && <Music className="w-12 h-12 text-orange-400" />}
                    {activeTab === 'presentations' && <Presentation className="w-12 h-12 text-pink-400" />}
                  </div>

                  {/* Content Info */}
                  <div className="p-4">
                    <h3 className="font-medium text-white mb-1 truncate">
                      {item.name}
                    </h3>
                    <p className="text-sm text-gray-400 mb-2">
                      {formatDate(item.created_at)}
                    </p>
                    <p className="text-xs text-gray-500 mb-3">
                      {formatFileSize(item.size)}
                    </p>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button className="flex-1 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm transition-colors flex items-center justify-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>View</span>
                      </button>
                      <button className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition-colors flex items-center justify-center">
                        <Download className="w-3 h-3" />
                      </button>
                      <button className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm transition-colors flex items-center justify-center">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Content Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">
                Create New {tabs.find(t => t.id === createType)?.name.slice(0, -1)}
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter title..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Describe what you want to create..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Persona
                </label>
                <select className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="cherry">Cherry (Creative)</option>
                  <option value="sophia">Sophia (Strategic)</option>
                  <option value="karen">Karen (Operational)</option>
                </select>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CreativeStudio

