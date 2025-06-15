import { Bot, Code, Play, Settings } from 'lucide-react'

export default function AgentFactory() {
  return (
    <div className="flex h-full">
      {/* Template Library */}
      <div className="w-80 bg-card border-r border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-6">Agent Templates</h2>
        
        <div className="space-y-4">
          <div className="p-4 border border-border rounded-xl hover:border-primary/50 transition-colors cursor-pointer">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Assistant Agent</h3>
                <p className="text-xs text-muted-foreground">General purpose</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Versatile AI assistant for customer support, Q&A, and general interactions
            </p>
            <div className="flex gap-2 mt-3">
              <span className="px-2 py-1 bg-blue-500/10 text-blue-500 text-xs rounded">Support</span>
              <span className="px-2 py-1 bg-blue-500/10 text-blue-500 text-xs rounded">Q&A</span>
              <span className="px-2 py-1 bg-blue-500/10 text-blue-500 text-xs rounded">Chat</span>
            </div>
          </div>

          <div className="p-4 border border-border rounded-xl hover:border-primary/50 transition-colors cursor-pointer">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-red-500/10 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Creative Agent</h3>
                <p className="text-xs text-muted-foreground">Content creation</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Specialized in content creation, writing, design, and creative problem-solving
            </p>
            <div className="flex gap-2 mt-3">
              <span className="px-2 py-1 bg-red-500/10 text-red-500 text-xs rounded">Writing</span>
              <span className="px-2 py-1 bg-red-500/10 text-red-500 text-xs rounded">Design</span>
              <span className="px-2 py-1 bg-red-500/10 text-red-500 text-xs rounded">Creative</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border bg-card">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Agent Factory</h1>
              <p className="text-muted-foreground">Create, configure, and deploy AI agents</p>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-accent hover:bg-accent/80 text-accent-foreground rounded-lg transition-colors">
                <Settings className="w-4 h-4 mr-2 inline" />
                Config
              </button>
              <button className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
                <Play className="w-4 h-4 mr-2 inline" />
                Deploy
              </button>
            </div>
          </div>
        </div>

        {/* Visual Builder */}
        <div className="flex-1 p-6">
          <div className="h-full border-2 border-dashed border-border rounded-xl flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Assistant Agent</h3>
              <p className="text-muted-foreground mb-6">
                Versatile AI assistant for customer support, Q&A, and general interactions with advanced natural language processing capabilities.
              </p>
              
              <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
                <div className="p-4 bg-card border border-border rounded-lg">
                  <h4 className="font-medium text-foreground mb-2">Natural Language Processing</h4>
                  <p className="text-sm text-muted-foreground">Advanced text understanding and generation</p>
                </div>
                <div className="p-4 bg-card border border-border rounded-lg">
                  <h4 className="font-medium text-foreground mb-2">Context Awareness</h4>
                  <p className="text-sm text-muted-foreground">Maintains conversation context and memory</p>
                </div>
                <div className="p-4 bg-card border border-border rounded-lg">
                  <h4 className="font-medium text-foreground mb-2">Multi-turn Dialogue</h4>
                  <p className="text-sm text-muted-foreground">Supports complex conversation flows</p>
                </div>
                <div className="p-4 bg-card border border-border rounded-lg">
                  <h4 className="font-medium text-foreground mb-2">Knowledge Integration</h4>
                  <p className="text-sm text-muted-foreground">Access to external knowledge sources</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Code Editor Panel */}
        <div className="h-64 border-t border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground">Agent Configuration</h3>
            <button className="p-2 rounded-lg hover:bg-accent transition-colors">
              <Code className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>
          
          <div className="bg-background border border-border rounded-lg p-4 font-mono text-sm">
            <div className="text-green-400"># Agent Configuration</div>
            <div className="text-blue-400">name: <span className="text-yellow-400">"Assistant Agent"</span></div>
            <div className="text-blue-400">type: <span className="text-yellow-400">"assistant"</span></div>
            <div className="text-blue-400">version: <span className="text-yellow-400">"1.0.0"</span></div>
            <div className="text-green-400"># Core Settings</div>
            <div className="text-blue-400">model:</div>
            <div className="ml-4 text-blue-400">provider: <span className="text-yellow-400">"openai"</span></div>
            <div className="ml-4 text-blue-400">name: <span className="text-yellow-400">"gpt-4"</span></div>
            <div className="ml-4 text-blue-400">temperature: <span className="text-purple-400">0.7</span></div>
            <div className="ml-4 text-blue-400">max_tokens: <span className="text-purple-400">2048</span></div>
          </div>
        </div>
      </div>
    </div>
  )
}

