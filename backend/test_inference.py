import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.ml_service import get_text_prediction
    
    print("\n--- RUNNING INFERENCE TEST ---")
    test_text = "I've been feeling really down and hopeless lately. Everything is just too much."
    print(f"Input: {test_text}")
    
    result = get_text_prediction(test_text)
    
    print("\nResult:")
    print(result)
    
    if result.get("risk_level"):
        print("\n[SUCCESS] INFERENCE SUCCESSFUL!")
    else:
        print("\n[FAILED] INFERENCE FAILED! No risk_level returned.")
        
except Exception as e:
    print(f"\n[ERROR] TEST FAILED WITH EXCEPTION: {e}")
