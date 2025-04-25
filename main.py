# main.py
#!/usr/bin/env python3
import argparse
import os
import shutil
import time
import random
from datetime import datetime
from dotenv import load_dotenv
import sys
import re
from typing import Optional, List # Added typing

# Import core components
from core.gemini_processor import process_all_products
from core.csv_processor import add_csv_output
from core.reporting_utils import report
# Import retailer auditor classes
from retailers.homedepot import HomeDepotAuditor
from retailers.lowes import LowesAuditor

def detect_retailer(url: str) -> Optional[str]:
    """Detects the retailer from the URL."""
    url_lower = url.lower()
    if "homedepot.com" in url_lower:
        return "homedepot"
    elif "lowes.com" in url_lower:
        return "lowes"
    # Add more retailers here if needed
    else:
        print(f"Warning: Could not determine retailer for URL: {url}")
        return None


def parse_selection(selection_str):
    """Parses the comma-separated selection string into a list of integers."""
    if not selection_str: return None
    try:
        indices = [int(i.strip()) for i in selection_str.split(',') if i.strip()]
        if not indices: raise ValueError("Selection cannot be empty.")
        if any(i <= 0 for i in indices): raise ValueError("Selected indices must be positive.")
        return indices
    except ValueError as e:
        print(f"Error: Invalid format for --select: '{selection_str}'. Use comma-separated positive integers. {e}")
        sys.exit(1)

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Audit product listings on Home Depot and Lowe's")
    parser.add_argument("--input-file", "-i", default="links.txt", help="Text file with product URLs (default: links.txt)")
    parser.add_argument("--output-folder", "-o", default="output", help="Output folder (default: 'output')")
    parser.add_argument("--delay", "-d", type=int, default=0, help="Optional delay before starting (seconds)")
    parser.add_argument("--retries", "-r", type=int, default=3, help="Number of capture attempts per link (default: 3)")
    parser.add_argument("--gemini", "-g", action="store_true", help="Run Gemini analysis on existing files")
    parser.add_argument("--csv", "-c", action="store_true", help="Generate/update CSV from existing analysis files")
    parser.add_argument("--csv-file", "-f", default="audit_results.csv", help="Name of the output CSV file (default: 'audit_results.csv')")
    parser.add_argument("--select", "-s", type=str, default=None, help="Select specific link numbers (1-based index) to process (e.g., 1,3,5)")
    parser.add_argument("--skip-capture", action="store_true", help="Skip the screenshot/text capture step")


    args = parser.parse_args()
    selected_indices = parse_selection(args.select)
    if selected_indices: print(f"Processing selectively for link numbers: {selected_indices}")

    if not os.path.exists(args.output_folder):
        try: os.makedirs(args.output_folder); print(f"Created output folder: {args.output_folder}")
        except OSError as e: print(f"FATAL: Could not create output folder '{args.output_folder}': {e}"); sys.exit(1)

    run_capture = not args.skip_capture and not args.gemini and not args.csv
    run_gemini = args.gemini
    run_csv = args.csv or args.gemini # Run CSV if explicitly requested OR after Gemini

    if run_capture:
        print("\n===== CAPTURING SCREENSHOTS & TEXT =====\n")
        if args.delay > 0:
            print(f"Waiting {args.delay} seconds before starting...")
            time.sleep(args.delay)

        links_processed_capture = 0
        try:
            if not os.path.exists(args.input_file):
                raise FileNotFoundError(f"Input file '{args.input_file}' not found.")

            with open(args.input_file, 'r') as f:
                links = [line.strip() for line in f if line.strip()]
            print(f"Found {len(links)} links in {args.input_file}")
            if not links: print("Input file is empty. No links to process."); sys.exit(0)

            for i, url in enumerate(links, 1):
                if selected_indices and i not in selected_indices: continue

                links_processed_capture += 1
                product_id_base = f"link{i}"
                retailer = detect_retailer(url)

                if not retailer:
                    report.start_product(f"{product_id_base}_unknown")
                    report.fail_product(f"{product_id_base}_unknown", f"Could not determine retailer for URL: {url}")
                    continue

                product_id_with_retailer = f"{product_id_base}_{retailer}"
                report.start_product(product_id_with_retailer) # Start report before attempt

                auditor = None
                if retailer == "homedepot":
                    auditor = HomeDepotAuditor()
                elif retailer == "lowes":
                    auditor = LowesAuditor()
                else:
                    report.fail_product(product_id_with_retailer, f"Unsupported retailer '{retailer}'")
                    continue

                print(f"\nProcessing {product_id_with_retailer} (Link #{i}, Retailer: {retailer}): {url}")
                output_base = os.path.join(args.output_folder, product_id_with_retailer)

                # Retry loop for capture
                success = False
                last_error = "Capture not attempted."
                for attempt in range(args.retries):
                    try:
                        print(f"Attempt {attempt + 1} of {args.retries}")
                        success, error_msg = auditor.capture_product_data(url, output_base)
                        last_error = error_msg
                        if success:
                            print(f"Successfully captured data for {product_id_with_retailer}")
                            report.pass_product(product_id_with_retailer)
                            break
                        else:
                             print(f"Capture attempt {attempt + 1} failed: {error_msg}")
                             if attempt < args.retries - 1:
                                 wait_time = 10 + (random.random() * 10)
                                 print(f"Waiting {wait_time:.1f}s before retrying...")
                                 time.sleep(wait_time)
                    except Exception as e:
                        last_error = f"Critical error during capture attempt {attempt + 1}: {e}"
                        print(f"ERROR: {last_error}")
                        if attempt < args.retries - 1:
                             wait_time = 15 + (random.random() * 10)
                             print(f"Waiting {wait_time:.1f}s before retrying after critical error...")
                             time.sleep(wait_time)

                if not success:
                    print(f"Failed to capture data for {product_id_with_retailer} after {args.retries} attempts.")
                    report.fail_product(product_id_with_retailer, f"Capture failed. Last error: {last_error}")

                # Wait between links logic
                remaining_links_to_process = False
                if selected_indices:
                    if any(sel_idx > i for sel_idx in selected_indices): remaining_links_to_process = True
                elif i < len(links): remaining_links_to_process = True
                if remaining_links_to_process:
                    wait_time = 5 + (random.random() * 10)
                    print(f"\nWaiting {wait_time:.1f} seconds before next link...")
                    time.sleep(wait_time)

            if links_processed_capture == 0 and selected_indices:
                 print(f"\nWarning: No links matched the selection criteria: {selected_indices}")
            print("\nScreenshot/Text capture complete!")

        except FileNotFoundError as e:
             print(f"Error: {e}")
             report.fail_product("Capture Setup", f"Input file error: {e}")
        except Exception as e:
             print(f"An unexpected error occurred during capture phase: {e}")
             report.fail_product("Capture Error", f"Unexpected error: {e}")


    # --- Gemini Analysis Step ---
    if run_gemini:
        print("\n===== RUNNING GEMINI ANALYSIS =====\n")
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Error: GEMINI_API_KEY not found in environment variables or .env file.")
            report.fail_product("Gemini Setup", "API Key Missing")
        else:
            process_all_products(
                args.output_folder,
                api_key=api_key,
                print_summary=False,
                selected_indices=selected_indices
            )
            print("\nAnalysis complete!")

    # --- CSV Generation Step ---
    if run_csv:
        print("\n===== GENERATING/UPDATING CSV FILE =====\n")
        add_csv_output(
            args.output_folder,
            args.csv_file,
            args.input_file,
            print_summary=False,
            selected_indices=selected_indices
        )
        print("\nCSV processing complete!")

    # --- Final Summary ---
    print("\n===== FINAL REPORT SUMMARY =====\n")
    if not report.product_status:
         if selected_indices: print("No products matched the selection criteria or processing failed.")
         else: print("No products were processed. Check input/output folders and logs.")
    else:
        report.print_summary()
        report_file = report.save_report(args.output_folder)
        print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    core_dir = "core"
    if not os.path.exists(core_dir):
        print(f"Warning: Core directory '{core_dir}' not found. Ensure files were moved previously.")

    main()