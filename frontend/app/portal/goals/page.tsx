'use client';

import { useEffect, useState } from 'react';

interface GoalAssignment {
  id: number;
  name: string;
  goal?: { id: number; name: string; code: string; weight: number };
  cycle?: { id: number; name: string };
  target_value: number;
  unit?: string;
  actual_value: number;
  completion_rate: number;
  state: string;
}

export default function PortalGoalsPage() {
  const [goals, setGoals] = useState<GoalAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/med-goals/my-goals', { cache: 'no-store' });
        const json = await res.json();
        if (!res.ok || json.status !== 'ok') {
          throw new Error(json.message || 'Failed to load goals');
        }
        setGoals(json.assignments || []);
      } catch (e: any) {
        setErr(e.message || String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <p>Loading goals…</p>;
  if (err) return <p>Error: {err}</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">My Goals</h1>
      {goals.length === 0 ? (
        <p>No goals assigned in this cycle.</p>
      ) : (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th align="left">Goal</th>
              <th>Cycle</th>
              <th>Target</th>
              <th>Actual</th>
              <th>% Completion</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {goals.map((g) => (
              <tr key={g.id}>
                <td>
                  <div className="font-medium">{g.goal?.name || g.name}</div>
                  <div className="text-xs opacity-70">{g.goal?.code}</div>
                </td>
                <td align="center">{g.cycle?.name || '—'}</td>
                <td align="right">
                  {g.target_value} {g.unit}
                </td>
                <td align="right">
                  {g.actual_value} {g.unit}
                </td>
                <td align="right">{g.completion_rate.toFixed(1)}%</td>
                <td align="center">{g.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
