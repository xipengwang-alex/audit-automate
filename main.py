#!/usr/bin/env python3
import argparse
import os
import shutil
from datetime import datetime
from link_processor import process_links_from_file
from gemini_processor import process_all_products
from csv_processor import add_csv_output
from reporting_utils import report
from dotenv import load_dotenv

def main():
    """
    Main entry point for the Home Depot product details screenshot tool.
    Handles command-line arguments and runs the appropriate function.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Take screenshots of Home Depot product details from multiple links")
    parser.add_argument("--input-file", "-i", default="links.txt", 
                        help="Text file with one product URL per line (default: links.txt)")
    parser.add_argument("--output-folder", "-o", default="output", 
                        help="Output folder for screenshots and text (default: 'output')")
    parser.add_argument("--delay", "-d", type=int, default=0,
                       help="Optional delay in seconds before starting (to allow manual proxy setup)")
    parser.add_argument("--retries", "-r", type=int, default=3,
                       help="Number of attempts to make if initial attempts fail (default: 3)")
    parser.add_argument("--prompt-file", "-p", default="prompt.txt",
                       help="Path to the prompt file for Gemini analysis (default: 'prompt.txt')")
    parser.add_argument("--gemini", "-g", action="store_true",
                       help="Run Gemini analysis on existing files in the output folder")
    parser.add_argument("--csv", "-c", action="store_true",
                       help="Generate a CSV file from existing analysis files")
    parser.add_argument("--csv-file", "-f", default="audit_results.csv",
                       help="Name of the output CSV file (default: 'audit_results.csv')")
    
    args = parser.parse_args()
    
    # Create output folder if it doesn't exist
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
        print(f"Created output folder: {args.output_folder}")
    
    # If --csv flag is provided, only generate the CSV file
    if args.csv:
        print("\n===== GENERATING CSV FILE =====\n")
        add_csv_output(args.output_folder, args.csv_file, args.input_file)
        print("\nCSV generation complete!")
    # If --gemini flag is provided, run the Gemini analysis and then generate CSV
    elif args.gemini:
        print("\n===== RUNNING GEMINI ANALYSIS =====\n")
        # Get API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Error: GEMINI_API_KEY not found in environment variables or .env file.")
            print("Please set this variable in a .env file with the format: GEMINI_API_KEY=your_api_key_here")
            return
        
        process_all_products(
            args.output_folder,
            args.prompt_file,
            api_key
        )
        print("\nAnalysis complete! All products have been processed.")
        
        # Automatically generate CSV after Gemini analysis
        print("\n===== GENERATING CSV FILE =====\n")
        add_csv_output(args.output_folder, args.csv_file, args.input_file)
        print("\nCSV generation complete!")
    # Otherwise, just process the links to capture screenshots
    else:
        print("\n===== CAPTURING SCREENSHOTS =====\n")
        process_links_from_file(
            args.input_file, 
            args.output_folder, 
            args.retries, 
            args.delay
        )
        print("\nAll links have been processed!")
    
    # Print final overall report summary
    print("\n===== FINAL REPORT SUMMARY =====\n")
    report.print_summary()
    report_file = report.save_report(args.output_folder)
    print(f"\nDetailed report saved to: {report_file}")

    # Create a copy of the CSV in the audit_report folder if it was generated
    if args.csv or args.gemini:
        try:
            import shutil
            csv_path = os.path.join(args.output_folder, args.csv_file)
            audit_report_folder = os.path.join(args.output_folder, "audit_report")
            if not os.path.exists(audit_report_folder):
                os.makedirs(audit_report_folder)
            
            if os.path.exists(csv_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_report_path = os.path.join(audit_report_folder, f"audit_results_{timestamp}.csv")
                shutil.copy2(csv_path, csv_report_path)
                print(f"CSV file copied to: {csv_report_path}")
        except Exception as e:
            print(f"Warning: Could not copy CSV file to audit_report folder: {str(e)}")

if __name__ == "__main__":
    main()