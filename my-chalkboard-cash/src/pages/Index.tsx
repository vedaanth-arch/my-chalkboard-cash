import { useEffect, useState } from "react";
import { DollarSign, Hash } from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { ExpenseCalendar } from "@/components/ExpenseCalendar";
import { ExpenseChart } from "@/components/ExpenseChart";
import { ExpenseComparisonChart } from "@/components/ExpenseComparisonChart";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ScanReceipt from "@/components/ScanReceipt";
import Investments from "@/components/Investments";
import { fetchBalance, fetchExpenseCount } from "@/lib/api";
import { API_BASE_URL } from "@/lib/api";

const Index = () => {
  const SAMPLE = (((import.meta as any)?.env?.VITE_SAMPLE_MODE) ?? 'true') === 'true';
  const [chartView, setChartView] = useState(50);
  const [balance, setBalance] = useState<string>("Loading...");
  const [expenseCount, setExpenseCount] = useState<number>(0);
  const [refreshToken, setRefreshToken] = useState(0);
  const [sampleMode, setSampleMode] = useState<boolean>(SAMPLE);

  const refreshStats = async () => {
    try {
      const [b, c] = await Promise.all([fetchBalance(), fetchExpenseCount()]);
      setBalance(`$${b.balance.toFixed(2)}`);
      setExpenseCount(c.count ?? 0);
      // bump token so charts/calendar re-fetch
      setRefreshToken((t) => t + 1);
    } catch {
      // fallbacks
    }
  };

  useEffect(() => {
    refreshStats();
  }, []);

  // Load persisted sample setting and persist on change
  useEffect(() => {
    const saved = window.localStorage.getItem("sampleMode");
    if (saved === "true" || saved === "false") {
      setSampleMode(saved === "true");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("sampleMode", sampleMode ? "true" : "false");
    // nudge charts to reload when mode flips
    setRefreshToken((t) => t + 1);
  }, [sampleMode]);

  return (
    <div className="min-h-screen bg-white p-6 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Navigation Tabs */}
        <Tabs defaultValue="tracker" className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-2">
            <TabsTrigger value="tracker">Tracker</TabsTrigger>
            <TabsTrigger value="investments">Investments</TabsTrigger>
          </TabsList>
          
          <TabsContent value="tracker" className="space-y-8 mt-8">
            {/* Header */}
            <div className="space-y-2">
              <h1 className="text-4xl md:text-5xl font-bold">Expense Tracker</h1>
              <p className="text-muted-foreground">Track and manage your daily expenses</p>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="sample-mode" checked={sampleMode} onCheckedChange={setSampleMode} />
              <label htmlFor="sample-mode" className="text-sm text-muted-foreground select-none">Sample data</label>
            </div>

        {/* Receipt Scanner Section */}
  <ScanReceipt onUpdated={refreshStats} />

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StatCard
            title="Total Balance"
            value={balance}
            icon={DollarSign}
            trend="This month"
          />
          <StatCard
            title="Total Expenses (Count)"
            value={String(expenseCount)}
            icon={Hash}
            trend="All-time entries"
          />
        </div>

        {/* Calendar Section */}
  <ExpenseCalendar refreshToken={refreshToken} useSample={sampleMode} />

        {/* Charts Section */}
        <div className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Weekly Analysis</h2>
            <p className="text-muted-foreground text-sm">
              Use the slider to switch between Week 1 and Week 2
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className={`transition-opacity duration-300 ${chartView > 30 ? 'opacity-100' : 'opacity-40'}`}>
              <ExpenseChart type="week1" refreshToken={refreshToken} useSample={sampleMode} />
            </div>
            <div className={`transition-opacity duration-300 ${chartView < 70 ? 'opacity-100' : 'opacity-40'}`}>
              <ExpenseChart type="week2" refreshToken={refreshToken} useSample={sampleMode} />
            </div>
          </div>

          {/* Slider Control */}
          <div className="max-w-md mx-auto space-y-4 pt-4">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span className={chartView < 50 ? 'text-primary font-semibold' : ''}>Week 1</span>
              <span className={chartView > 50 ? 'text-secondary font-semibold' : ''}>Week 2</span>
            </div>
            <Slider
              value={[chartView]}
              onValueChange={(value) => setChartView(value[0])}
              max={100}
              step={1}
              className="w-full"
            />
          </div>

          {/* Comparison Chart */}
          <div className="pt-6">
            <ExpenseComparisonChart key={refreshToken} useSample={sampleMode} />
          </div>
        </div>
          </TabsContent>
          
          <TabsContent value="investments" className="mt-8">
            <Investments />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
