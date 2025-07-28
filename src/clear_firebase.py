#!/usr/bin/env python3
"""
Utility script to manage Firebase data for the LLM Mafia Game Competition.
"""

import sys
import argparse
from firebase_manager import FirebaseManager


def main():
    parser = argparse.ArgumentParser(description="Manage Firebase data for LLM Mafia Game")
    parser.add_argument(
        "--action", 
        choices=["summary", "clear"], 
        required=True,
        help="Action to perform: 'summary' to see data counts, 'clear' to delete all data"
    )
    parser.add_argument(
        "--confirm", 
        action="store_true",
        help="Required flag to confirm data deletion (only for 'clear' action)"
    )
    
    args = parser.parse_args()
    
    # Initialize Firebase manager
    firebase = FirebaseManager()
    
    if not firebase.initialized:
        print("❌ Firebase not initialized. Check your credentials.")
        sys.exit(1)
    
    if args.action == "summary":
        print("📊 Getting Firebase data summary...")
        summary = firebase.get_data_summary()
        
        if summary.get("total_documents", 0) == 0:
            print("✅ Firebase is empty - no data to clear.")
        else:
            print(f"📈 Found {summary['total_documents']} documents total")
            
    elif args.action == "clear":
        if not args.confirm:
            print("⚠️  WARNING: This will permanently delete ALL game data from Firebase!")
            print("   This includes:")
            print("   - All game results")
            print("   - All game logs")
            print("   - All statistics")
            print()
            print("   To proceed, run:")
            print(f"   python {sys.argv[0]} --action clear --confirm")
            sys.exit(0)
        
        print("🗑️  Clearing all Firebase data...")
        success = firebase.clear_all_data(confirm=True)
        
        if success:
            print("✅ All Firebase data cleared successfully!")
            print("🚀 Ready for new experiment!")
        else:
            print("❌ Failed to clear Firebase data.")
            sys.exit(1)


if __name__ == "__main__":
    main()