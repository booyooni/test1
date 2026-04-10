#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from analytics import create_comprehensive_eda_dashboard
    print("✅ EDA function imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")

try:
    from utils import load_processed_data
    print("✅ Utils function imported successfully!")
    df = load_processed_data()
    print(f"✅ Data loaded successfully! Shape: {df.shape}")
except Exception as e:
    print(f"❌ Data loading error: {e}")