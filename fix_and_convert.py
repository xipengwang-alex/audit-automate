#!/usr/bin/env python3
import os
import argparse
import re
import csv
import shutil
from datetime import datetime
from reporting_utils import report

def fix_analysis_files(folder_path, print_summary=False):
    """
    Fix the format of existing analysis files.
    
    Args:
        folder_path: Folder containing analysis text files
        print_summary: Whether to print and save report summary at the end
    """
    # Import reporting utility
    from reporting_utils import report
    
    # Define the expected fields in the correct order
    expected_fields = [
        "Link",
        "Category",
        "SKU",
        "Retailer",
        "Images Count",
        "Images Visible Issues?",
        "Video Count",
        "Video Visible Issues?",
        "A+ Content Type",
        "A+ Content Accuracy?",
        "Title Actual",
        "Title Accuracy?",
    ]
    
    # Add bullet points (up to 9)
    for i in range(1, 10):
        expected_fields.append(f"Bullet Point {i} Actual")
        expected_fields.append(f"Bullet Point {i} Accuracy?")
        
    # Add description
    expected_fields.extend([
        "Description Actual",
        "Description Accuracy?",
    ])
    
    # Get all analysis text files
    analysis_files = [f for f in os.listdir(folder_path) if f.endswith('_analysis.txt')]
    
    if not analysis_files:
        print(f"No analysis files found in '{folder_path}'.")
        return
    
    # Process each analysis file
    for file in analysis_files:
        # Extract product ID (e.g., "link1" from "link1_analysis.txt")
        match = re.match(r'(link\d+)', file)
        product_id = match.group(1) if match else os.path.splitext(file)[0].replace('_analysis', '')
        
        # Start product processing in report
        report.start_product(product_id)
        
        try:
            file_path = os.path.join(folder_path, file)
            print(f"Fixing {file}...")
            
            # Read the content of the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if all expected fields are present
            missing_fields = []
            for field in expected_fields:
                if f"**{field}:**" not in content:
                    missing_fields.append(field)
            
            corrected_content = content
            
            # If fields are missing, add them at the end with empty values
            if missing_fields:
                print(f"  Warning: {len(missing_fields)} fields are missing. Adding empty fields...")
                for field in missing_fields:
                    corrected_content += f"\n**{field}:**"
            
            # Ensure each field is on its own line and has the correct format
            formatted_lines = []
            
            # Use regex to find all field lines (including multiline values)
            pattern = r'\*\*(.*?):\*\*(.*?)(?=\*\*\w+:\*\*|$)'
            matches = re.findall(pattern, corrected_content, re.DOTALL)
            
            # Create a dictionary to store field values
            field_values = {}
            for match in matches:
                field_name = match[0].strip()
                field_value = match[1].strip()
                field_values[field_name] = field_value
            
            # Ensure all fields are present in the correct order
            for field in expected_fields:
                value = field_values.get(field, "")
                formatted_lines.append(f"**{field}:** {value}")
            
            # Join lines with newlines
            formatted_content = "\n".join(formatted_lines)
            
            # Write the corrected content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"  Fixed and saved: {file_path}")
            report.pass_product(product_id)
            
        except Exception as e:
            error_msg = f"Error fixing {file}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            report.fail_product(product_id, error_msg)
            
    # Only print summary if requested
    if print_summary:
        report.print_summary()
        report.save_report(folder_path)

def create_csv(folder_path, csv_filename, links_file="links.txt", print_summary=False):
    """
    Create a CSV file from analysis text files.
    
    Args:
        folder_path: Folder containing analysis text files
        csv_filename: Name of the output CSV file
        links_file: Path to the file containing product URLs (one per line)
        print_summary: Whether to print and save report summary at the end
    """
    # Define the expected fields in the correct order
    expected_fields = [
        "Link",
        "Category",
        "SKU",
        "Retailer",
        "Images Count",
        "Images Visible Issues?",
        "Video Count",
        "Video Visible Issues?",
        "A+ Content Type",
        "A+ Content Accuracy?",
        "Title Actual",
        "Title Accuracy?",
    ]
    
    # Add bullet points (up to 9)
    for i in range(1, 10):
        expected_fields.append(f"Bullet Point {i} Actual")
        expected_fields.append(f"Bullet Point {i} Accuracy?")
        
    # Add description
    expected_fields.extend([
        "Description Actual",
        "Description Accuracy?",
    ])
    
    # Load URLs from links.txt
    url_map = {}
    try:
        if os.path.exists(links_file):
            with open(links_file, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                url = line.strip()
                if url:
                    url_map[f"link{i}"] = url
                    
            print(f"Loaded {len(url_map)} URLs from {links_file}")
        else:
            print(f"Warning: Links file '{links_file}' not found.")
    except Exception as e:
        print(f"Error loading URLs from {links_file}: {str(e)}")
    
    # Get all analysis text files
    analysis_files = [f for f in os.listdir(folder_path) if f.endswith('_analysis.txt')]
    
    if not analysis_files:
        print(f"No analysis files found in '{folder_path}'.")
        return
    
    # Create CSV file
    report_folder = os.path.join(folder_path, "audit_report")
    if not os.path.exists(report_folder):
        os.makedirs(report_folder)
    
    csv_path = os.path.join(folder_path, csv_filename)
    
    # Also create a timestamped copy in the audit_report folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_report_path = os.path.join(report_folder, f"audit_results_{timestamp}.csv")
    
    # Write to both locations
    try:
        # Main output folder CSV
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=expected_fields)
            writer.writeheader()
            
            # Process each analysis file
            for file in sorted(analysis_files):
                # Extract product ID (e.g., "link1" from "link1_analysis.txt")
                match = re.match(r'(link\d+)', file)
                product_id = match.group(1) if match else os.path.splitext(file)[0].replace('_analysis', '')
                
                # Start product processing in report
                report.start_product(product_id)
                
                try:
                    file_path = os.path.join(folder_path, file)
                    print(f"Processing {file} for CSV...")
                    
                    # Extract link number from file name (e.g., "link1" from "link1_analysis.txt")
                    link_match = re.match(r'(link\d+)', file)
                    link_key = link_match.group(1) if link_match else None
                    
                    # Read the content of the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract field values using regex
                    data = {}
                    for field in expected_fields:
                        # Skip Link field if we'll set it from url_map
                        if field == "Link" and link_key and link_key in url_map:
                            continue
                            
                        escaped_field = re.escape(field)
                        pattern = fr'\*\*{escaped_field}:\*\*(.*?)(?=\*\*\w+:\*\*|$)'
                        matches = re.findall(pattern, content, re.DOTALL)
                        
                        if matches:
                            # Clean up the value (remove leading/trailing whitespace)
                            value = matches[0].strip()
                            data[field] = value
                        else:
                            data[field] = ""
                    
                    # Set URL from links.txt if available
                    if link_key and link_key in url_map:
                        data["Link"] = url_map[link_key]
                        print(f"  Matched {link_key} with URL: {url_map[link_key]}")
                    else:
                        print(f"  No URL match found for {file}")
                    
                    # Check if Link field is filled
                    if not data.get("Link", "").strip():
                        print(f"  WARNING: No URL found for {product_id}")
                    
                    # Write the row to the CSV
                    writer.writerow(data)
                    
                    # Mark as passed in report
                    report.pass_product(product_id)
                    
                except Exception as e:
                    error_msg = f"Error processing {file}: {str(e)}"
                    print(f"  ERROR: {error_msg}")
                    report.fail_product(product_id, error_msg)
                    continue
        
        # Also save a copy to the audit_report folder
        import shutil
        shutil.copy2(csv_path, csv_report_path)
        
        print(f"CSV file created: {csv_path}")
        print(f"CSV file also saved to: {csv_report_path}")
        
        # Only print summary if requested
        if print_summary:
            report.print_summary()
            report.save_report(folder_path)
    
    except Exception as e:
        print(f"Error creating CSV files: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Fix analysis files and create a CSV file")
    parser.add_argument("--folder", "-f", default="output", help="Folder containing analysis files (default: 'output')")
    parser.add_argument("--csv-file", "-c", default="audit_results.csv", help="Name of the output CSV file (default: 'audit_results.csv')")
    parser.add_argument("--links-file", "-l", default="links.txt", help="Path to the links file (default: 'links.txt')")
    parser.add_argument("--fix-only", action="store_true", help="Only fix the analysis files, don't create a CSV")
    parser.add_argument("--csv-only", action="store_true", help="Only create a CSV file, don't fix the analysis files")
    
    args = parser.parse_args()
    
    # Import reporting utility
    from reporting_utils import report
    
    print(f"\n{'='*80}")
    print(f"STARTING FILE PROCESSING: {args.folder}")
    print(f"{'='*80}")
    
    # Process based on flags
    if args.csv_only:
        create_csv(args.folder, args.csv_file, args.links_file, print_summary=False)
    elif args.fix_only:
        fix_analysis_files(args.folder, print_summary=False)
    else:
        # Default: fix files and then create CSV
        fix_analysis_files(args.folder, print_summary=False)
        create_csv(args.folder, args.csv_file, args.links_file, print_summary=False)
    
    # Print and save final report
    print(f"\n{'='*80}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*80}")
    report.print_summary()
    report_file = report.save_report(args.folder)
    print(f"Detailed report saved to: {report_file}")
    
    print(f"\n{'='*80}")
    print(f"PROCESSING COMPLETE!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()