import { useEffect, useState } from "react";
import { TrendingUp, DollarSign, PieChart, Wallet } from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { Card } from "@/components/ui/card";
import { getRecommendations } from "@/lib/api";

type Rec = { symbol: string; price: number; shares: number };

export default function Investments() {
  const [recs, setRecs] = useState<Rec[]>([]);
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await getRecommendations();
        setRecs(data.recommendations || []);
        setBalance(data.balance || 0);
      } catch (e: any) {
        console.error(e);
        setError(e.message || "Failed to load recommendations");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totalPortfolio = recs.reduce((acc, s) => acc + s.price * s.shares, 0);
  const activeInvestments = recs.length;

  return (
    <div className="space-y-8">
      <h1 className="text-4xl md:text-5xl font-bold">Investment Portfolio</h1>
      <p className="text-muted-foreground">Track and manage your investments</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Portfolio Value"
          value={`$${totalPortfolio.toFixed(2)}`}
          icon={Wallet}
          trend={`Current Balance: $${balance.toFixed(2)}`}
        />
        <StatCard title="Total Returns" value="$0.00" icon={TrendingUp} trend="Realtime calculation" />
        <StatCard title="Active Investments" value={activeInvestments.toString()} icon={PieChart} trend="Diversified" />
        <StatCard title="Monthly Dividends" value="$0.00" icon={DollarSign} trend="Passive income" />
      </div>

      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Investment Summary</h2>
        {loading && <p className="text-sm text-muted-foreground">Loading recommendations…</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="space-y-4">
          {recs.map((s) => (
            <div key={s.symbol} className="flex justify-between items-center p-4 bg-muted/50 rounded-lg">
              <div>
                <p className="font-semibold">{s.symbol}</p>
                <p className="text-sm text-muted-foreground">Price: ${s.price.toFixed(2)}</p>
              </div>
              <p className="text-lg font-bold">{s.shares} shares (${(s.shares * s.price).toFixed(2)})</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
