#!/usr/bin/env python3
import argparse
import os
from link_processor import process_links_from_file
from gemini_processor import process_all_products
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
    
    args = parser.parse_args()
    
    # If --gemini flag is provided, only run the Gemini analysis
    if args.gemini:
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

if __name__ == "__main__":
    main()