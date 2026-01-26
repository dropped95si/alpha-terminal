import pandas as pd
import os
from market_ai_kit.scanner.feature_engine import FeatureEngine
from market_ai_kit.scanner.learning_loop import DynamicLearner

def bootstrap():
    print("🚀 INITIALIZING V2.20 STATISTICAL CORE...")
    
    # 1. Load History
    # If you don't have this CSV, the system will start with default neutral weights (safe).
    csv_path = 'data/historical_trades.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ '{csv_path}' not found. Initializing with NEUTRAL weights.")
        learner = DynamicLearner()
        learner._save_weights() # Save defaults
        print("✅ Default weights created.")
        return

    print(f"📂 Loading history from {csv_path}...")
    try:
        raw_df = pd.read_csv(csv_path)
        
        # 2. Transform Features
        print("⚙️  Running Feature Engine...")
        engine = FeatureEngine()
        processed_df = engine.transform(raw_df)

        # 3. Train the Brain
        print("🧠 Calibrating Statistical Weights...")
        learner = DynamicLearner()
        learner.train(processed_df)
        print("✅ SYSTEM CALIBRATED. Weights saved to 'config/learned_weights.json'.")
        
    except Exception as e:
        print(f"❌ Error during bootstrap: {e}")

if __name__ == "__main__":
    bootstrap()