#!/usr/bin/env python3
import os
import argparse
import re
import csv

def fix_analysis_files(folder_path):
    """
    Fix the format of existing analysis files.
    
    Args:
        folder_path: Folder containing analysis text files
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
    
    # Get all analysis text files
    analysis_files = [f for f in os.listdir(folder_path) if f.endswith('_analysis.txt')]
    
    if not analysis_files:
        print(f"No analysis files found in '{folder_path}'.")
        return
    
    # Process each analysis file
    for file in analysis_files:
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

def create_csv(folder_path, csv_filename, links_file="links.txt"):
    """
    Create a CSV file from analysis text files.
    
    Args:
        folder_path: Folder containing analysis text files
        csv_filename: Name of the output CSV file
        links_file: Path to the file containing product URLs (one per line)
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
    csv_path = os.path.join(folder_path, csv_filename)
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=expected_fields)
        writer.writeheader()
        
        # Process each analysis file
        for file in sorted(analysis_files):
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
                
                # Write the row to the CSV
                writer.writerow(data)
            except Exception as e:
                print(f"Error processing {file}: {str(e)}. Skipping this file.")
                continue
        
        print(f"CSV file created: {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Fix analysis files and create a CSV file")
    parser.add_argument("--folder", "-f", default="output", help="Folder containing analysis files (default: 'output')")
    parser.add_argument("--csv-file", "-c", default="audit_results.csv", help="Name of the output CSV file (default: 'audit_results.csv')")
    parser.add_argument("--links-file", "-l", default="links.txt", help="Path to the links file (default: 'links.txt')")
    parser.add_argument("--fix-only", action="store_true", help="Only fix the analysis files, don't create a CSV")
    parser.add_argument("--csv-only", action="store_true", help="Only create a CSV file, don't fix the analysis files")
    
    args = parser.parse_args()
    
    # Process based on flags
    if args.csv_only:
        create_csv(args.folder, args.csv_file, args.links_file)
    elif args.fix_only:
        fix_analysis_files(args.folder)
    else:
        # Default: fix files and then create CSV
        fix_analysis_files(args.folder)
        create_csv(args.folder, args.csv_file, args.links_file)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()