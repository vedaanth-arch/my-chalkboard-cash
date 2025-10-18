import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "@/components/ui/use-toast";
import { uploadReceipt, fetchExpenseCount, fetchBalance, API_BASE_URL } from "@/lib/api";

type Props = { onUpdated?: () => void };

export default function ScanReceipt({ onUpdated }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [manualAmount, setManualAmount] = useState<string>("");

  const handleUpload = async () => {
    if (!file) return alert("Select a receipt image");
    setIsLoading(true);
    try {
      // Use Flask OCR endpoint that also updates balance/count
      const fd = new FormData();
      fd.append("file", file);
      const u = new URL("/ocr/receipt", API_BASE_URL);
      const res = await fetch(u.toString(), { method: "POST", body: fd });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Failed to scan receipt");
  setData(json);
  onUpdated?.();
      toast({ title: "Receipt scanned", description: `Total: $${json.parsed?.total ?? "?"} · Count: ${json.count ?? "?"}` });
    } catch (e: any) {
      console.error(e);
      toast({ title: "Scan failed", description: e.message || "Failed to scan receipt" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddExpense = async () => {
    const amount = parseFloat(manualAmount);
    if (isNaN(amount) || amount <= 0) {
      toast({ title: "Invalid amount", description: "Please enter a number greater than 0" });
      return;
    }
    try {
      const u = new URL("/expenses/add", API_BASE_URL);
      const res = await fetch(u.toString(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Failed to add expense");
      toast({ title: "Expense added", description: `New total: $${json.total.toFixed?.(2) ?? json.total} · Count: ${json.count ?? '—'}` });
  setDialogOpen(false);
      setManualAmount("");
  onUpdated?.();
    } catch (e: any) {
      console.error(e);
      toast({ title: "Error", description: e.message || "Could not add expense" });
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle>Scan Your Receipt</CardTitle>
            <CardDescription>Upload a receipt image to extract expense details</CardDescription>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="accent" size="sm">Add Expense</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Expense</DialogTitle>
                <DialogDescription>Quickly add a manual expense amount</DialogDescription>
              </DialogHeader>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground" htmlFor="amount">Amount</label>
                <Input id="amount" type="number" step="0.01" placeholder="e.g. 25.99" value={manualAmount} onChange={(e)=>setManualAmount(e.target.value)} />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={()=>setDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleAddExpense}>Add</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input type="file" accept="image/*" onChange={e=>setFile(e.target.files?.[0]||null)} disabled={isLoading}/>
        <Button onClick={handleUpload} disabled={!file||isLoading} className="w-full">
          {isLoading ? "Scanning..." : "Upload & Scan"}
        </Button>
        {data && (
          <div className="mt-6 p-4 rounded-lg border bg-card space-y-3">
            <p><strong>Date:</strong> {data.parsed.date}</p>
            <p><strong>Total:</strong> {data.parsed.total}</p>
            <p><strong>Items:</strong> {data.parsed.items.map((i:any)=>i.name+"("+i.price+")").join(", ")}</p>
            <p><strong>Balance:</strong> ${data.balance ?? data.parsed?.remaining}</p>
            <p><strong>Expense Count:</strong> {data.count ?? "—"}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
