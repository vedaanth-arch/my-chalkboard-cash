import asyncio
import json

import httpx


async def main():
    base = "http://127.0.0.1:8000"
    async with httpx.AsyncClient(timeout=10) as client:
        for path in ["/health", "/expenses/weekly?month=1&year=2025&seed=123", "/calendar/month?month=1&year=2025&seed=123"]:
            r = await client.get(base + path)
            r.raise_for_status()
            print(path, "->", r.status_code)
            data = r.json()
            print(json.dumps({k: (v if k != 'week1' else v[:2]) for k, v in data.items()} if isinstance(data, dict) else data[:2], indent=2))


if __name__ == "__main__":
    asyncio.run(main())