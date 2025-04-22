import os
import csv
import re

class CsvProcessor:
    """
    Process Gemini analysis results and output to a consolidated CSV file.
    """
    
    def __init__(self, output_folder, csv_filename="audit_results.csv"):
        """
        Initialize the CSV processor.
        
        Args:
            output_folder: Folder containing analysis text files
            csv_filename: Name of the output CSV file
        """
        self.output_folder = output_folder
        self.csv_filename = os.path.join(output_folder, csv_filename)
        
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
    
    def _parse_analysis_file(self, file_path):
        """
        Parse an analysis file and extract field values.
        
        Args:
            file_path: Path to the analysis text file
            
        Returns:
            dict: Parsed fields and values
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create a dictionary to store all field values
            parsed_data = {field: "" for field in self.expected_fields}
            
            # Extract each field value using regex
            for field in self.expected_fields:
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
            return {field: "" for field in self.expected_fields}
    
    def process_all_analyses(self):
        """
        Process all analysis files and output to a CSV file.
        
        Returns:
            bool: Whether processing was successful
        """
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
            # Create CSV file
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.expected_fields)
                writer.writeheader()
                
                # Process each analysis file
                for file in sorted(analysis_files):
                    file_path = os.path.join(self.output_folder, file)
                    print(f"Processing {file}...")
                    
                    # Parse the analysis file
                    parsed_data = self._parse_analysis_file(file_path)
                    
                    # Write to CSV
                    writer.writerow(parsed_data)
            
            print(f"Successfully created CSV file: {self.csv_filename}")
            return True
            
        except Exception as e:
            print(f"Error creating CSV file: {str(e)}")
            return False


def add_csv_output(output_folder="output", csv_filename="audit_results.csv"):
    """
    Process all analysis files and output to a CSV file.
    
    Args:
        output_folder: Folder containing analysis text files
        csv_filename: Name of the output CSV file
        
    Returns:
        bool: Whether processing was successful
    """
    processor = CsvProcessor(output_folder, csv_filename)
    return processor.process_all_analyses()