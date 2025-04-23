# c:\Users\wangx\Dropbox\Purdue\APEC Water\audit-automate\main.py
#!/usr/bin/env python3
import argparse
import os
import shutil
from datetime import datetime
from link_processor import process_links_from_file
from gemini_processor import process_all_products
from csv_processor import add_csv_output # Keep add_csv_output, CsvProcessor handles selection internally
from reporting_utils import report
from dotenv import load_dotenv
import sys # Import sys for exiting

def parse_selection(selection_str):
    """Parses the comma-separated selection string into a list of integers."""
    if not selection_str:
        return None # No selection
    try:
        indices = [int(i.strip()) for i in selection_str.split(',') if i.strip()]
        if not indices:
            raise ValueError("Selection cannot be empty.")
        if any(i <= 0 for i in indices):
             raise ValueError("Selected indices must be positive integers.")
        return indices
    except ValueError as e:
        print(f"Error: Invalid format for --select argument '{selection_str}'. Use comma-separated positive integers (e.g., 1,3,5). {e}")
        sys.exit(1) # Exit if parsing fails

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
                       help="Generate or update a CSV file from existing analysis files")
    parser.add_argument("--csv-file", "-f", default="audit_results.csv",
                       help="Name of the output CSV file (default: 'audit_results.csv')")
    parser.add_argument("--select", "-s", type=str, default=None,
                        help="Select specific link numbers (1-based index) to process, comma-separated (e.g., 1,3,5)")

    args = parser.parse_args()

    # Parse the selection string
    selected_indices = parse_selection(args.select)
    if selected_indices:
        print(f"Processing selectively for link numbers: {selected_indices}")

    # Create output folder if it doesn't exist
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
        print(f"Created output folder: {args.output_folder}")

    # --- Execution Logic ---
    action_taken = False

    # If --csv flag is provided, only generate/update the CSV file
    if args.csv:
        action_taken = True
        print("\n===== GENERATING/UPDATING CSV FILE =====\n")
        add_csv_output(
            args.output_folder,
            args.csv_file,
            args.input_file,
            print_summary=False, # Summary printed at the end
            selected_indices=selected_indices # Pass selection
        )
        print("\nCSV processing complete!")

    # If --gemini flag is provided, run the Gemini analysis and then generate/update CSV
    elif args.gemini:
        action_taken = True
        print("\n===== RUNNING GEMINI ANALYSIS =====\n")
        # Get API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Error: GEMINI_API_KEY not found in environment variables or .env file.")
            print("Please set this variable in a .env file with the format: GEMINI_API_KEY=your_api_key_here")
            return # Exit main

        process_all_products(
            args.output_folder,
            args.prompt_file,
            api_key,
            print_summary=False, # Summary printed at the end
            selected_indices=selected_indices # Pass selection
        )
        print("\nAnalysis complete!")

        # Automatically generate/update CSV after Gemini analysis
        print("\n===== GENERATING/UPDATING CSV FILE =====\n")
        add_csv_output(
            args.output_folder,
            args.csv_file,
            args.input_file,
            print_summary=False, # Summary printed at the end
            selected_indices=selected_indices # Pass selection
        )
        print("\nCSV processing complete!")

    # Default: process links to capture screenshots/text (respecting selection)
    elif not action_taken: # Only run if -c or -g wasn't specified
        action_taken = True
        print("\n===== CAPTURING SCREENSHOTS & TEXT =====\n")
        process_links_from_file(
            args.input_file,
            args.output_folder,
            args.retries,
            args.delay,
            print_summary=False, # Summary printed at the end
            selected_indices=selected_indices # Pass selection
        )
        print("\nScreenshot/Text capture complete!")

    # --- Final Summary ---
    # Print final overall report summary for actions performed
    print("\n===== FINAL REPORT SUMMARY =====\n")
    if not report.product_status: # Check if any products were actually processed
         if selected_indices:
             print("No products matched the selection criteria or processing failed for selected items.")
         else:
             print("No products were processed. Check input file or output folder.")
    else:
        report.print_summary()
        report_file = report.save_report(args.output_folder)
        print(f"\nDetailed report saved to: {report_file}")

    # Create a copy of the CSV in the audit_report folder if it was generated/updated
    if args.csv or args.gemini:
        try:
            csv_path = os.path.join(args.output_folder, args.csv_file)
            audit_report_folder = os.path.join(args.output_folder, "audit_report")
            if not os.path.exists(audit_report_folder):
                os.makedirs(audit_report_folder)

            if os.path.exists(csv_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Include selection info in filename if applicable
                selection_tag = f"_selection_{'_'.join(map(str, selected_indices))}" if selected_indices else ""
                csv_report_filename = f"audit_results{selection_tag}_{timestamp}.csv"
                csv_report_path = os.path.join(audit_report_folder, csv_report_filename)

                shutil.copy2(csv_path, csv_report_path)
                print(f"CSV file copy saved to: {csv_report_path}")
        except Exception as e:
            print(f"Warning: Could not copy CSV file to audit_report folder: {str(e)}")

if __name__ == "__main__":
    main()