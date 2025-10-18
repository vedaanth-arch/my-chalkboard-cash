export type DaySeries = { day: string; expenses: number };

export type WeeklyResponse = {
  week1: DaySeries[];
  week2: DaySeries[];
  comparison: { day: string; week1: number; week2: number }[];
};

export type CalendarResponse = {
  month: number;
  year: number;
  days: { day: number; expense: number; income: number }[];
};

export type OCRResponse = {
  text: string;
  parsed: {
    total: number;
    remaining: number;
    date: string | null;
    items: { name: string; price: number }[];
  };
  balance?: number;
  count?: number;
};

export type RecommendationResponse = {
  balance: number;
  recommendations: {
    symbol: string;
    price: number;
    shares: number;
  }[];
};

// 👇 Backend URL resolution
const DEFAULT_BASE = "http://127.0.0.1:5000";
const ENV: any = (import.meta as any)?.env ?? {};
function resolveBase(): string {
  const direct = ENV.VITE_API_BASE_URL as string | undefined;
  if (direct && /^https?:\/\//i.test(direct)) return direct;
  const host = (ENV.VITE_API_HOST as string | undefined)?.trim();
  const scheme = ((ENV.VITE_API_SCHEME as string | undefined) || "https").trim();
  const port = (ENV.VITE_API_PORT as string | undefined)?.trim();
  if (host) {
    // Prefer scheme://host and ignore port for hosted platforms where public URL embeds the portless host
    // Optionally include port for non-standard http dev setups
    const needsPort = scheme === "http" && port && port !== "80" && !host.includes(":");
    return `${scheme}://${host}${needsPort ? ":" + port : ""}`;
  }
  return direct || DEFAULT_BASE;
}
export const API_BASE_URL = resolveBase();

// Generic handler
async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// --- ⚙️ OCR Receipt Upload ---
export async function uploadReceipt(file: File): Promise<OCRResponse> {
  const u = new URL("/ocr/receipt", API_BASE_URL);
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(u.toString(), { method: "POST", body: fd });
  return handle<OCRResponse>(res);
}

// --- ⚙️ Stock Recommendations ---
export async function getRecommendations(): Promise<RecommendationResponse> {
  const u = new URL("/investments/recommend", API_BASE_URL);
  const res = await fetch(u.toString());
  return handle<RecommendationResponse>(res);
}

// --- ⚙️ Current Balance ---
export async function fetchBalance(): Promise<{ balance: number }> {
  const u = new URL("/expenses/balance", API_BASE_URL);
  const res = await fetch(u.toString());
  return handle<{ balance: number }>(res);
}

export async function fetchExpenseCount(): Promise<{ count: number }> {
  const u = new URL("/expenses/count", API_BASE_URL);
  const res = await fetch(u.toString());
  return handle<{ count: number }>(res);
}

// --- ⚙️ Optional: Weekly & Calendar (can be ignored if not used) ---
export async function fetchWeekly(params?: {
  month?: number;
  year?: number;
  seed?: number;
}): Promise<WeeklyResponse> {
  const u = new URL("/expenses/weekly", API_BASE_URL);
  if (params?.month) u.searchParams.set("month", String(params.month));
  if (params?.year) u.searchParams.set("year", String(params.year));
  if (params?.seed != null) u.searchParams.set("seed", String(params.seed));
  const res = await fetch(u.toString());
  return handle<WeeklyResponse>(res);
}

export async function fetchCalendar(params?: {
  month?: number;
  year?: number;
  seed?: number;
}): Promise<CalendarResponse> {
  const u = new URL("/calendar/month", API_BASE_URL);
  if (params?.month) u.searchParams.set("month", String(params.month));
  if (params?.year) u.searchParams.set("year", String(params.year));
  if (params?.seed != null) u.searchParams.set("seed", String(params.seed));
  const res = await fetch(u.toString());
  return handle<CalendarResponse>(res);
}

// --- ⚙️ Add manual expense ---
export async function addExpense(amount: number): Promise<{ total: number; balance: number; count?: number }> {
  const u = new URL("/expenses/add", API_BASE_URL);
  const res = await fetch(u.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  });
  return handle<{ total: number; balance: number; count?: number }>(res);
}
