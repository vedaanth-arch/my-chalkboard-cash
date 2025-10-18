import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { fetchWeekly } from "@/lib/api";

export const ExpenseComparisonChart = ({ useSample = true }: { useSample?: boolean }) => {
  const [comparisonData, setComparisonData] = useState<{ day: string; week1: number; week2: number }[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const genSample = useMemo(() => {
    const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
    const rnd = (seed: number) => { let x = Math.sin(seed) * 10000; return x - Math.floor(x); };
    return days.map((d, i) => ({ day: d, week1: Math.round(50 + rnd(i+1)*150), week2: Math.round(60 + rnd(i+11)*160) }));
  }, []);

  useEffect(() => {
    if (useSample) {
      setComparisonData(genSample);
      setError(null);
      return;
    }
    let mounted = true;
    (async () => {
      try {
        const res = await fetchWeekly();
        if (!mounted) return;
        setComparisonData(res.comparison);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message ?? "Failed to load weekly comparison");
      }
    })();
    return () => { mounted = false; };
  }, [useSample, genSample]);

  return (
    <Card className="p-6 bg-card border-border h-full">
      <h3 className="text-xl font-bold mb-2">Week 1 vs Week 2 Comparison</h3>
      <p className="text-sm text-muted-foreground mb-6">Daily expense comparison between both weeks</p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={comparisonData ?? []}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="day" 
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              color: 'hsl(var(--foreground))'
            }}
          />
          <Legend 
            wrapperStyle={{ 
              color: 'hsl(var(--foreground))',
              fontSize: '14px'
            }}
          />
          <Bar 
            dataKey="week1" 
            fill="hsl(var(--chart-1))" 
            radius={[8, 8, 0, 0]}
            name="Week 1"
          />
          <Bar 
            dataKey="week2" 
            fill="hsl(var(--chart-2))" 
            radius={[8, 8, 0, 0]}
            name="Week 2"
          />
        </BarChart>
      </ResponsiveContainer>
      {error && <div className="text-sm text-red-500 mt-2">{error}</div>}
      {!error && !comparisonData && <div className="text-sm text-muted-foreground mt-2">Loading…</div>}
    </Card>
  );
};
