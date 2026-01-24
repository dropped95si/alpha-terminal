import os
from dotenv import load_dotenv
from supabase import create_client
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

load_dotenv()

def verify():
    print("\n🚀 ALPHA TERMINAL - PRODUCTION KEY AUDIT")
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        supabase.table("signals").select("ticker").limit(1).execute()
        print("✅ SUPABASE: Connection Solid.")
    except Exception as e: print(f"❌ SUPABASE: FAILED. {e}")

    try:
        client = StockHistoricalDataClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))
        res = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols="ANET"))
        print(f"✅ ALPACA: Connection Solid. Live ANET Ask: ${res['ANET'].ask_price:.2f}")
    except Exception as e: print(f"❌ ALPACA: FAILED. {e}")

if __name__ == "__main__": verify()
