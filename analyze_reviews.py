# -*- coding: utf-8 -*-

"""
Standalone script to analyze Google Maps reviews using AI.

Usage:
    python analyze_reviews.py <path_to_csv_file>
    
Example:
    python analyze_reviews.py C:\\Users\\5lin6\\.gemini\\antigravity\\scratch\\output\\khosh-cafe_reviews.csv
"""

import sys
import os
from review_analyzer import ReviewAnalyzer

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("=" * 70)
        print("GOOGLE MAPS REVIEW ANALYZER")
        print("=" * 70)
        print("\nUsage:")
        print(f"  python {os.path.basename(__file__)} <path_to_csv_file>")
        print("\nExample:")
        print(f"  python {os.path.basename(__file__)} output\\khosh-cafe_reviews.csv")
        print("\nNote: Make sure to set your OPENAI_API_KEY in a .env file or as an environment variable")
        print("=" * 70)
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.isfile(csv_path):
        print(f"[ERROR] File not found: {csv_path}")
        sys.exit(1)
    
    # Check if it's a CSV file
    if not csv_path.lower().endswith('.csv'):
        print(f"[ERROR] File must be a CSV file: {csv_path}")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        print("[INFO] Initializing OpenAI analyzer...")
        analyzer = ReviewAnalyzer()
        
        # Generate output path
        output_path = csv_path.replace('.csv', '_analysis_report.txt')
        
        # Analyze reviews
        print(f"[INFO] Analyzing reviews from: {csv_path}")
        results = analyzer.analyze_reviews_from_csv(csv_path, output_path)
        
        if results:
            print("\n[SUCCESS] Analysis complete!")
            print(f"[INFO] Text report saved to: {output_path}")
            print(f"[INFO] JSON results saved to: {csv_path.replace('.csv', '_analysis.json')}")
        else:
            print("\n[ERROR] Analysis failed or no results generated")
            sys.exit(1)
            
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("\nTo fix this:")
        print("1. Create a .env file in this directory")
        print("2. Add your OpenAI API key: OPENAI_API_KEY=your_key_here")
        print("3. Get an API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
