/**
 * Admin LLM Configuration Page
 * Main entry point for LLM configuration management
 */

import { LLMConfiguration } from '@/components/admin/LLMConfiguration';

export default function LLMAdminPage() {
  return (
    <div className="min-h-screen bg-background">
      <LLMConfiguration />
    </div>
  );
}