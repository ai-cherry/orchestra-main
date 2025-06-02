import React from 'react';
import { Search, Mic, Upload } from 'lucide-react';
import { Button } from '../../ui/button';
import { InputMode } from './index';

interface InputModeSelectorProps {
  inputMode: InputMode;
  setInputMode: (mode: InputMode) => void;
}

export const InputModeSelector: React.FC<InputModeSelectorProps> = ({
  inputMode,
  setInputMode,
}) => {
  const modes: { id: InputMode; icon: React.ElementType; tooltip: string }[] = [
    { id: 'text', icon: Search, tooltip: 'Text search' },
    { id: 'voice', icon: Mic, tooltip: 'Voice search' },
    { id: 'file', icon: Upload, tooltip: 'File upload' },
  ];

  return (
    <div className="flex gap-1">
      {modes.map((mode) => (
        <Button
          key={mode.id}
          variant="outline"
          size="icon"
          onClick={() => setInputMode(mode.id)}
          className={inputMode === mode.id ? 'orchestrator-btn-outline active' : 'orchestrator-btn-outline'}
          title={mode.tooltip}
        >
          <mode.icon className="w-4 h-4" />
        </Button>
      ))}
    </div>
  );
};