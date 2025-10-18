import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { fetchWeekly, type DaySeries } from "@/lib/api";

interface ExpenseChartProps {
  type: "week1" | "week2";
  refreshToken?: number;
  useSample?: boolean;
}

export const ExpenseChart = ({ type, refreshToken, useSample = true }: ExpenseChartProps) => {
  const [week1Data, setWeek1Data] = useState<DaySeries[] | null>(null);
  const [week2Data, setWeek2Data] = useState<DaySeries[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Sample data generator (deterministic)
  const genSample = useMemo(() => {
    const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
    const rnd = (seed: number) => { let x = Math.sin(seed) * 10000; return x - Math.floor(x); };
    const w1 = days.map((d, i) => ({ day: d, expenses: Math.round(50 + rnd(i+1)*150) }));
    const w2 = days.map((d, i) => ({ day: d, expenses: Math.round(60 + rnd(i+11)*160) }));
    return { w1, w2 };
  }, []);

  useEffect(() => {
    if (useSample) {
      setWeek1Data(genSample.w1);
      setWeek2Data(genSample.w2);
      setError(null);
      return;
    }
    let mounted = true;
    (async () => {
      try {
        const res = await fetchWeekly();
        if (!mounted) return;
        setWeek1Data(res.week1);
        setWeek2Data(res.week2);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message ?? "Failed to load weekly data");
      }
    })();
    return () => { mounted = false; };
  }, [refreshToken, useSample, genSample]);

  const data = type === "week1" ? (week1Data ?? []) : (week2Data ?? []);
  const title = type === "week1" ? "Week 1 Expenses" : "Week 2 Expenses";
  const ChartComponent = type === "week1" ? BarChart : LineChart;

  return (
    <Card className="p-6 bg-card border-border h-full">
      <h3 className="text-xl font-bold mb-6">{title}</h3>
      {error && <div className="text-sm text-red-500 mb-2">{error}</div>}
      {!error && data.length === 0 && <div className="text-sm text-muted-foreground">Loading…</div>}
      <ResponsiveContainer width="100%" height={300}>
        {type === "week1" ? (
          <BarChart data={data}>
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
            <Bar 
              dataKey="expenses" 
              fill="hsl(var(--chart-1))" 
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        ) : (
          <LineChart data={data}>
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
            <Line 
              type="monotone" 
              dataKey="expenses" 
              stroke="hsl(var(--chart-2))" 
              strokeWidth={3}
              dot={{ fill: 'hsl(var(--chart-2))', r: 5 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </Card>
  );
};
