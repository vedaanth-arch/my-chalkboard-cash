import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchCalendar, type CalendarResponse } from "@/lib/api";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";

interface DayData {
  day: number;
  expense: number;
  income: number;
}

export const ExpenseCalendar = ({ refreshToken, useSample = true }: { refreshToken?: number; useSample?: boolean }) => {
  const [currentDate] = useState(new Date());
  const [calendar, setCalendar] = useState<CalendarResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sample, setSample] = useState<Record<number, { expense: number; income: number }>>({});
  const [editingDay, setEditingDay] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<number>(50);

  useEffect(() => {
    if (useSample) {
      // generate sample percentages for the month (expense 20-80, saving complement)
      const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
      const rnd = (seed: number) => {
        let x = Math.sin(seed) * 10000; return x - Math.floor(x);
      };
      const s: Record<number, { expense: number; income: number }> = {};
      for (let d = 1; d <= daysInMonth; d++) {
        const r = rnd(d + currentDate.getMonth() * 37 + currentDate.getFullYear());
        const exp = Math.round(20 + r * 60); // 20..80
        s[d] = { expense: exp, income: 100 - exp };
      }
      setSample(s);
      return; // skip backend in sample mode
    }
    let mounted = true;
    const load = async () => {
      try {
        const res = await fetchCalendar({ month: currentDate.getMonth() + 1, year: currentDate.getFullYear() });
        if (!mounted) return;
        setCalendar(res);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message ?? "Failed to load calendar data");
      }
    };
    load();
    // light polling for background updates (1 min)
    const id = setInterval(load, 60_000);
    return () => { mounted = false; clearInterval(id); };
  }, [currentDate, refreshToken, useSample]);

  const monthName = currentDate.toLocaleString('default', { month: 'long' });
  const year = currentDate.getFullYear();
  
  const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  // Get first day of month (0 = Sunday, 1 = Monday, etc.)
  const firstDay = new Date(year, currentDate.getMonth(), 1).getDay();
  const adjustedFirstDay = firstDay === 0 ? 6 : firstDay - 1; // Adjust so Monday is 0
  
  const daysInMonth = new Date(year, currentDate.getMonth() + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, currentDate.getMonth(), 0).getDate();
  
  const daysData: DayData[] = useMemo(() => {
    const daysInMonth = new Date(year, currentDate.getMonth() + 1, 0).getDate();
    const map: Record<number, DayData> = {};
    for (let d = 1; d <= daysInMonth; d++) {
      map[d] = { day: d, expense: 0, income: 0 };
    }
    if (useSample) {
      for (let d = 1; d <= daysInMonth; d++) {
        const s = sample[d];
        if (s) map[d] = { day: d, expense: s.expense, income: s.income };
      }
    } else if (calendar?.days) {
      for (const di of calendar.days) {
        map[di.day] = { day: di.day, expense: di.expense, income: di.income };
      }
    }
    return Object.values(map);
  }, [calendar, currentDate, year, useSample, sample]);

  // Compute normalization baseline for visual percent; prefer day totals if available, otherwise normalize by max expense in month
  const maxExpense = useMemo(() => {
    if (useSample) return 100; // percentages
    const m = Math.max(0, ...daysData.map((d) => d.expense || 0));
    return m > 0 ? m : 1;
  }, [daysData, useSample]);

  const getDayInfo = (day: number) => {
    return daysData.find(d => d.day === day) || { day, expense: 0, income: 0 };
  };
  
  const renderDayIndicator = (day: number) => {
    const info = getDayInfo(day);
    const dayTotal = (info.expense || 0) + (info.income || 0);
    const bothZero = (info.expense || 0) === 0 && (info.income || 0) === 0;
    // If we have explicit income, use true split; otherwise normalize expense against monthly max and complement as saving
    let expPct: number;
    if (bothZero) {
      expPct = 0;
    } else if (dayTotal > 0) {
      expPct = Math.max(0, Math.min(1, (info.expense || 0) / dayTotal));
    } else {
      expPct = Math.max(0, Math.min(1, (info.expense || 0) / maxExpense));
    }
    const savPct = 1 - expPct;

    // Long oval (closed test tube) with stacked red(top)/green(bottom)
    return (
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {bothZero ? (
          <div className="h-12 w-5 rounded-full bg-muted/40 shadow-inner" />
        ) : (
          <div className="relative h-12 w-5 rounded-full bg-muted/30 overflow-hidden shadow-sm">
            <div className="absolute top-0 left-0 right-0 bg-expense" style={{ height: `${expPct * 100}%` }} />
            <div className="absolute bottom-0 left-0 right-0 bg-income" style={{ height: `${savPct * 100}%` }} />
          </div>
        )}
      </div>
    );
  };
  
  const renderCalendarDays = () => {
    const days = [];
    
    // Previous month days
    for (let i = adjustedFirstDay - 1; i >= 0; i--) {
      days.push(
        <div key={`prev-${i}`} className="text-center p-4 text-muted-foreground/40 relative">
          {daysInPrevMonth - i}
        </div>
      );
    }
    
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const info = getDayInfo(day);
      const total = (info.expense || 0) + (info.income || 0);
      const bothZero = (info.expense || 0) === 0 && (info.income || 0) === 0;
      const expPct = bothZero ? 0 : (total > 0 ? (info.expense || 0) / total : (info.expense || 0) / maxExpense);
      const savPct = bothZero ? 0 : 1 - Math.max(0, Math.min(1, expPct));
      days.push(
        <div
          key={day}
          className="text-center p-4 relative cursor-pointer hover:bg-accent/30 rounded-lg transition-colors"
          onClick={() => {
            if (!useSample) return; // manual edit only in sample mode
            setEditingDay(day);
            const info = getDayInfo(day);
            const total = (info.expense || 0) + (info.income || 0);
            const pct = total > 0 ? Math.round((info.expense || 0) * 100 / total) : 0;
            setEditValue(pct);
          }}
        >
          {renderDayIndicator(day)}
          <span className="relative z-10 font-medium">{day}</span>
        </div>
      );
    }
    
    // Next month days to fill grid
    const remainingDays = 42 - days.length;
    for (let day = 1; day <= remainingDays; day++) {
      days.push(
        <div key={`next-${day}`} className="text-center p-4 text-muted-foreground/40 relative">
          {day}
        </div>
      );
    }
    
    return days;
  };

  return (
    <Card className="p-6 bg-card border-border">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{year} Month 01 January</p>
          <h2 className="text-3xl font-bold">{monthName}</h2>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" className="hover:bg-accent">
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="icon" className="hover:bg-accent">
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>
      </div>
  {/* silent UI: no error/loading text per request */}
      
      <div className="grid grid-cols-8 gap-2 mb-4">
        <div className="text-center text-muted-foreground text-sm font-medium"></div>
        {daysOfWeek.map(day => (
          <div key={day} className="text-center text-muted-foreground text-sm font-medium">
            {day}
          </div>
        ))}
      </div>
      
      <div className="grid grid-cols-8 gap-2">
        <div className="flex flex-col gap-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="text-center text-muted-foreground text-sm p-4">
              {String(i + 1).padStart(2, '0')}
            </div>
          ))}
        </div>
        <div className="col-span-7 grid grid-cols-7 gap-2">
          {renderCalendarDays()}
        </div>
      </div>
      
      {/* legend removed per request */}

      {/* Manual editing dialog (iconless, immediate apply) */}
      <Dialog open={!!editingDay} onOpenChange={(o) => !o && setEditingDay(null)}>
        <DialogContent className="sm:max-w-[360px]">
          <div className="py-2">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-expense">Expense: {editValue}%</span>
              <span className="text-income">Saving: {100 - editValue}%</span>
            </div>
            <div className="mb-6">
              <Slider value={[editValue]} max={100} step={1} onValueChange={(v) => {
                const val = v[0] ?? 0;
                setEditValue(val);
                if (editingDay && useSample) {
                  setSample((prev) => ({
                    ...prev,
                    [editingDay]: { expense: val, income: 100 - val },
                  }));
                }
              }} />
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};
