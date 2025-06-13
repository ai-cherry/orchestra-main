import { usePersona } from '@/contexts/PersonaContext'

export function ChatInterface() {
  const { currentPersona, personaConfig } = usePersona()
  const currentPersonaConfig = personaConfig[currentPersona]

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="border-b border-border p-6">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full bg-${currentPersonaConfig.color}-500`} />
          <div>
            <h1 className="text-2xl font-bold">Chat with {currentPersonaConfig.name}</h1>
            <p className="text-muted-foreground">{currentPersonaConfig.description}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">Chat Interface</h2>
          <p className="text-muted-foreground">
            The chat interface will be enhanced in the next phase to integrate with the data processing pipeline.
          </p>
        </div>
      </div>
    </div>
  )
} 