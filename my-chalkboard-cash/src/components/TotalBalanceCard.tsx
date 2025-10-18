    import { useEffect, useState } from "react";
    import { fetchBalance } from "@/api";
    import { Card } from "@/components/ui/card";

    export default function TotalBalanceCard() {
    const [balance, setBalance] = useState<number | null>(null);

    useEffect(() => {
        fetchBalance()
        .then((data) => setBalance(data.balance))
        .catch((err) => console.error("Error fetching balance:", err));
    }, []);

    return (
        <Card className="p-6 bg-green-100 shadow-md">
        <h2 className="text-sm font-medium text-gray-500">Total Balance</h2>
        <p className="text-3xl font-bold text-gray-900">
            {balance !== null ? `$${balance.toFixed(2)}` : "Loading..."}
        </p>
        <p className="text-xs text-gray-500">This month</p>
        </Card>
    );
    }
