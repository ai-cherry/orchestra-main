import { useEffect, useState } from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { fetcher } from '@/lib/api';

interface MemoryStat { persona: string; items: number }

export default function MemoryPage() {
  const [stats, setStats] = useState<MemoryStat[]>([]);
  useEffect(() => {
    fetcher('/api/memory/stats').then((d) => setStats(d ?? [])).catch(() => {});
  }, []);
  return (
    <PageWrapper title="Memory Stats">
      <Card>
        <CardHeader>
          <CardTitle>Persona Memory Usage</CardTitle>
        </CardHeader>
        <CardContent>
          {stats.map((s) => (
            <div key={s.persona} className="flex justify-between py-1">
              <span>{s.persona}</span>
              <span>{s.items} items</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </PageWrapper>
  );
}
