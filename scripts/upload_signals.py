#!/usr/bin/env python3
import json
import subprocess
import os
from datetime import datetime
from supabase import create_client

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("https://gyilkjvdglnzbzioyqze.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5aWxranZkZ2xuemJ6aW95cXplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg3ODM2NTksImV4cCI6MjA4NDM1OTY1OX0.Zk2GQma5RBJPNR1u_3xiwVeXzptLpZPFOyh7uCIOMXg")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

# Run audit CLI with JSON output
print("🧠 Running signal scan...")
result = subprocess.run(
    ["python", "-m", "market_ai_kit.scanner.audit_v22",
     "--tickers", "NVDA", "TSLA", "AMD", "AAPL", "MSFT",
     "--json"],
    capture_output=True,
    text=True,
    cwd="."
)

if result.returncode != 0:
    print(f"❌ Scan failed: {result.stderr}")
    exit(1)

# Initialize Supabase client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Parse each signal
signals_added = 0
try:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if not line.strip() or line.startswith('==='):
            continue
        try:
            signal = json.loads(line)
            
            # Insert into Supabase
            response = client.table("signals").insert({
                "ticker": signal.get("ticker"),
                "probability": signal.get("p_up"),
                "confidence": signal.get("confidence"),
                "whale_verdict": signal.get("whale_verdict"),
                "credibility": signal.get("credibility"),
                "risk_level": signal.get("risk_level"),
                "recommendation": signal.get("recommendation"),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            signals_added += 1
            print(f"✅ {signal.get('ticker')}: {signal.get('p_up')}")
        except json.JSONDecodeError:
            continue

    print(f"\n🎉 {signals_added} signals uploaded to Supabase!")
    
except Exception as e:
    print(f"❌ Error uploading signals: {e}")
    exit(1)
