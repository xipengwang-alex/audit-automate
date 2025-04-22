import os
import csv
import re

class CsvProcessor:
    """
    Process Gemini analysis results and output to a consolidated CSV file.
    Uses links.txt to match product URLs with their corresponding output files.
    """
    
    def __init__(self, output_folder, csv_filename="audit_results.csv", links_file="links.txt"):
        """
        Initialize the CSV processor.
        
        Args:
            output_folder: Folder containing analysis text files
            csv_filename: Name of the output CSV file
            links_file: Path to the file containing product URLs (one per line)
        """
        self.output_folder = output_folder
        self.csv_filename = os.path.join(output_folder, csv_filename)
        self.links_file = links_file
        
        # Load URLs from links.txt
        self.url_map = self._load_urls_from_file()
        
        # Define the expected fields in the correct order
        self.expected_fields = [
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
            self.expected_fields.append(f"Bullet Point {i} Actual")
            self.expected_fields.append(f"Bullet Point {i} Accuracy?")
            
        # Add description
        self.expected_fields.extend([
            "Description Actual",
            "Description Accuracy?",
        ])
    
    def _load_urls_from_file(self):
        """
        Load URLs from links.txt file.
        
        Returns:
            dict: Mapping from link number (e.g., "link1") to URL
        """
        url_map = {}
        
        try:
            if not os.path.exists(self.links_file):
                print(f"Warning: Links file '{self.links_file}' not found.")
                return url_map
                
            with open(self.links_file, 'r') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                url = line.strip()
                if url:
                    url_map[f"link{i}"] = url
                    
            print(f"Loaded {len(url_map)} URLs from {self.links_file}")
            return url_map
            
        except Exception as e:
            print(f"Error loading URLs from {self.links_file}: {str(e)}")
            return url_map
    
    def _parse_analysis_file(self, file_path, file_name):
        """
        Parse an analysis file and extract field values.
        
        Args:
            file_path: Path to the analysis text file
            file_name: Name of the analysis file
            
        Returns:
            dict: Parsed fields and values
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create a dictionary to store all field values
            parsed_data = {field: "" for field in self.expected_fields}
            
            # Extract link number from file name (e.g., "link1" from "link1_analysis.txt")
            link_match = re.match(r'(link\d+)', file_name)
            link_key = link_match.group(1) if link_match else None
            
            # Set the URL based on the link number
            if link_key and link_key in self.url_map:
                parsed_data["Link"] = self.url_map[link_key]
                print(f"  Matched {link_key} with URL: {self.url_map[link_key]}")
            else:
                print(f"  No URL match found for {file_name}")
            
            # Extract each field value using regex
            for field in self.expected_fields:
                if field == "Link" and parsed_data["Link"]:
                    # Skip Link field if we already set it from url_map
                    continue
                    
                # Escape special regex characters in the field name
                escaped_field = re.escape(field)
                
                # Match the field and its value
                pattern = fr'\*\*{escaped_field}:\*\*(.*?)(?:\*\*|$)'
                matches = re.findall(pattern, content, re.DOTALL)
                
                if matches:
                    # Clean up the value (remove leading/trailing whitespace)
                    value = matches[0].strip()
                    parsed_data[field] = value
            
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            # Return a dictionary with empty values in case of error
            empty_data = {field: "" for field in self.expected_fields}
            
            # Try to still set the Link field if we can determine it from the filename
            try:
                link_match = re.match(r'(link\d+)', file_name)
                if link_match:
                    link_key = link_match.group(1)
                    if link_key in self.url_map:
                        empty_data["Link"] = self.url_map[link_key]
                        print(f"  Set URL for {file_name} despite parsing error: {self.url_map[link_key]}")
            except:
                pass
                
            return empty_data
    
    def process_all_analyses(self):
        """
        Process all analysis files and output to a CSV file.
        
        Returns:
            bool: Whether processing was successful
        """
        # Import reporting utility
        from reporting_utils import report
        import shutil
        from datetime import datetime
        
        # Check if output folder exists
        if not os.path.exists(self.output_folder):
            print(f"Error: Output folder '{self.output_folder}' does not exist.")
            return False
        
        # Get all analysis text files
        analysis_files = [f for f in os.listdir(self.output_folder) if f.endswith('_analysis.txt')]
        
        if not analysis_files:
            print(f"No analysis files found in '{self.output_folder}'.")
            return False
        
        try:
            # Create CSV file in the main output folder
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.expected_fields)
                writer.writeheader()
                
                # Process each analysis file
                for file in sorted(analysis_files):
                    # Extract product ID (e.g., "link1" from "link1_analysis.txt")
                    match = re.match(r'(link\d+)', file)
                    product_id = match.group(1) if match else os.path.splitext(file)[0].replace('_analysis', '')
                    
                    # Start product processing in report
                    report.start_product(product_id)
                    
                    try:
                        file_path = os.path.join(self.output_folder, file)
                        print(f"Processing {file}...")
                        
                        # Parse the analysis file
                        parsed_data = self._parse_analysis_file(file_path, file)
                        
                        # Check if Link field is filled
                        if not parsed_data.get("Link", "").strip():
                            print(f"  WARNING: No URL found for {product_id}")
                        
                        # Write to CSV
                        writer.writerow(parsed_data)
                        
                        # Mark as passed in report
                        report.pass_product(product_id)
                        
                    except Exception as file_error:
                        error_msg = f"Error processing {file}: {str(file_error)}"
                        print(f"  ERROR: {error_msg}")
                        report.fail_product(product_id, error_msg)
                        continue
            
            # Create a copy in the audit_report folder
            report_folder = os.path.join(self.output_folder, "audit_report")
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_report_path = os.path.join(report_folder, f"audit_results_{timestamp}.csv")
            
            shutil.copy2(self.csv_filename, csv_report_path)
            
            print(f"Successfully created CSV file: {self.csv_filename}")
            print(f"CSV file also saved to: {csv_report_path}")
            return True
            
        except Exception as e:
            print(f"Error creating CSV file: {str(e)}")
            return False


def add_csv_output(output_folder="output", csv_filename="audit_results.csv", links_file="links.txt"):
    """
    Process all analysis files and output to a CSV file.
    
    Args:
        output_folder: Folder containing analysis text files
        csv_filename: Name of the output CSV file
        links_file: Path to the file containing product URLs (one per line)
        
    Returns:
        bool: Whether processing was successful
    """
    # Import reporting utility
    from reporting_utils import report
    
    print(f"\n{'='*80}")
    print(f"GENERATING CSV FILE: {csv_filename}")
    print(f"{'='*80}")
    
    processor = CsvProcessor(output_folder, csv_filename, links_file)
    success = processor.process_all_analyses()
    
    if success:
        report.print_summary()
        report.save_report(output_folder)
    
    return success