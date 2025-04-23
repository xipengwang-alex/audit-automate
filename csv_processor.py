# c:\Users\wangx\Dropbox\Purdue\APEC Water\audit-automate\csv_processor.py
import os
import csv
import re
import shutil
from datetime import datetime
from typing import List, Optional, Dict # Import typing helpers

class CsvProcessor:
    """
    Process Gemini analysis results and output to a consolidated CSV file.
    Uses links.txt to match product URLs with their corresponding output files.
    Supports updating existing CSV files selectively.
    """

    def __init__(self, output_folder, csv_filename="audit_results.csv", links_file="links.txt"):
        """
        Initialize the CSV processor.

        Args:
            output_folder: Folder containing analysis text files
            csv_filename: Name of the output CSV file (relative to output_folder)
            links_file: Path to the file containing product URLs (one per line)
        """
        self.output_folder = output_folder
        self.csv_filename = os.path.join(output_folder, csv_filename) # Full path to CSV
        self.links_file = links_file # Path relative to project root usually

        # Load URLs from links.txt - crucial for mapping analysis files to CSV rows
        self.url_map = self._load_urls_from_file()
        if not self.url_map:
             print("Warning: No URLs loaded. CSV 'Link' column might be incomplete or rely solely on analysis file content.")

        # Define the expected fields in the correct order
        self.expected_fields = [
            "Link", "Category", "SKU", "Retailer",
            "Images Count", "Images Visible Issues?",
            "Video Count", "Video Visible Issues?",
            "A+ Content Type", "A+ Content Accuracy?",
            "Title Actual", "Title Accuracy?",
        ]
        # Add bullet points (up to 9)
        for i in range(1, 10):
            self.expected_fields.append(f"Bullet Point {i} Actual")
            self.expected_fields.append(f"Bullet Point {i} Accuracy?")
        # Add description
        self.expected_fields.extend([
            "Description Actual", "Description Accuracy?",
        ])

        # Placeholder for existing CSV data (loaded when processing)
        self.existing_data = []
        self.url_to_row_index = {} # Map URL to index in existing_data

    def _load_urls_from_file(self) -> Dict[str, str]:
        """
        Load URLs from links.txt file.

        Returns:
            dict: Mapping from link number (e.g., "link1") to URL
        """
        url_map = {}
        try:
            if not os.path.exists(self.links_file):
                print(f"Warning: Links file '{self.links_file}' not found during CSV processing init.")
                return url_map

            with open(self.links_file, 'r') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                url = line.strip()
                if url:
                    url_map[f"link{i}"] = url

            print(f"CSV Processor: Loaded {len(url_map)} URLs from {self.links_file}")
            return url_map

        except Exception as e:
            print(f"Error loading URLs from {self.links_file} in CSV Processor: {str(e)}")
            return url_map # Return empty map on error

    def _load_existing_csv(self):
        """Loads data from the existing CSV file if it exists."""
        self.existing_data = []
        self.url_to_row_index = {}
        if not os.path.exists(self.csv_filename):
            print(f"CSV file '{self.csv_filename}' not found. Will create a new one.")
            return # Nothing to load

        try:
            with open(self.csv_filename, 'r', newline='', encoding='utf-8-sig') as csvfile: # Use utf-8-sig to handle BOM
                reader = csv.DictReader(csvfile)
                # Ensure all expected fields are present in the reader, even if missing in CSV header
                # This prevents errors if CSV is malformed or old
                reader.fieldnames = [field for field in self.expected_fields if field in reader.fieldnames] + \
                                    [field for field in self.expected_fields if field not in reader.fieldnames]

                self.existing_data = list(reader)
                print(f"Loaded {len(self.existing_data)} rows from existing CSV: {self.csv_filename}")

                # Create a map from URL to row index for quick updates
                for idx, row in enumerate(self.existing_data):
                    link = row.get("Link", "").strip()
                    if link:
                        # Normalize URL slightly (e.g., remove trailing slash) if needed
                        # link = link.rstrip('/')
                        self.url_to_row_index[link] = idx

        except Exception as e:
            print(f"Error reading existing CSV file '{self.csv_filename}': {str(e)}")
            print("Will proceed assuming an empty or new CSV.")
            self.existing_data = [] # Reset on error
            self.url_to_row_index = {}


    def _parse_analysis_file(self, file_path: str, file_name: str) -> Optional[Dict[str, str]]:
        """
        Parse an analysis file and extract field values.

        Args:
            file_path: Path to the analysis text file
            file_name: Name of the analysis file

        Returns:
            dict: Parsed fields and values, or None if parsing fails critically.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create a dictionary to store all field values, initialized empty
            parsed_data = {field: "" for field in self.expected_fields}

            # Extract link number from file name (e.g., "link1" from "link1_analysis.txt")
            link_match = re.match(r'(link\d+)', file_name)
            link_key = link_match.group(1) if link_match else None
            url_from_map = self.url_map.get(link_key, "") if link_key else ""

            # Use regex to find **Field:** Value pairs, handling multiline values
            # Case-insensitive matching for field names
            pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*?)(?=\*\*[a-zA-Z0-9\s\+\?\#]+:\*\*|\Z)', re.DOTALL | re.IGNORECASE)
            matches = pattern.findall(content)

            found_values = {}
            for match in matches:
                field_name_raw = match[0].strip()
                field_value = match[1].strip()
                # Normalize field name found in file for comparison
                normalized_name = ' '.join(field_name_raw.split())
                found_values[normalized_name] = field_value

            # Populate parsed_data using expected_fields order
            for field in self.expected_fields:
                value = ""
                found = False
                # Check against found values (case-insensitive)
                for found_field, found_val in found_values.items():
                    if found_field.lower() == field.lower():
                        value = found_val
                        found = True
                        break
                parsed_data[field] = value

            # Explicitly set the Link field from url_map if available and not already set correctly
            # Prioritize url_map over potentially incorrect value parsed from file
            if url_from_map:
                parsed_data["Link"] = url_from_map
                if link_key: print(f"  Matched {link_key} with URL from map: {url_from_map}")
            elif not parsed_data.get("Link"):
                 if link_key: print(f"  Warning: No URL found in url_map for {link_key}. 'Link' field might be empty or from analysis text.")

            return parsed_data

        except FileNotFoundError:
             print(f"Error: Analysis file not found: {file_path}")
             return None # Indicate failure
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            # Return a dictionary with empty values but try to set Link if possible
            empty_data = {field: "" for field in self.expected_fields}
            if link_key and link_key in self.url_map:
                empty_data["Link"] = self.url_map[link_key]
                print(f"  Set URL for {file_name} ({link_key}) despite parsing error: {self.url_map[link_key]}")
            return empty_data # Return fallback data


    def process_all_analyses(self, print_summary=False, selected_indices: Optional[List[int]] = None):
        """
        Process analysis files and output to a CSV file.
        Handles selective updates if selected_indices is provided.

        Args:
            print_summary: Whether to print and save report summary at the end (delegated)
            selected_indices: List of 1-based link indices to process for CSV update.
                              If None, process all analysis files found.
        Returns:
            bool: Whether processing was successful overall.
        """
        # Import reporting utility (careful with circular imports if moved)
        from reporting_utils import report # Assuming report is a global instance

        # Check if output folder exists
        if not os.path.exists(self.output_folder):
            print(f"Error: Output folder '{self.output_folder}' does not exist.")
            report.fail_product("CSV Gen Error", f"Output folder '{self.output_folder}' does not exist.")
            return False

        # --- Load existing CSV data ---
        self._load_existing_csv() # Populates self.existing_data and self.url_to_row_index

        # --- Filter analysis files based on selection ---
        all_analysis_files = [f for f in os.listdir(self.output_folder) if f.endswith('_analysis.txt')]
        files_to_process = []

        if selected_indices:
            print(f"CSV Processing: Selecting analysis files for indices: {selected_indices}")
            selected_filenames = {f"link{i}_analysis.txt" for i in selected_indices}
            files_to_process = [f for f in all_analysis_files if f in selected_filenames]
            if len(files_to_process) != len(selected_indices):
                 print(f"Warning: Found {len(files_to_process)} analysis files for {len(selected_indices)} selected indices. Some might be missing.")
                 missing_indices = []
                 for i in selected_indices:
                      if f"link{i}_analysis.txt" not in files_to_process:
                           missing_indices.append(i)
                 if missing_indices: print(f"  Missing analysis files for indices: {missing_indices}")

        else:
            print("CSV Processing: Processing all found analysis files.")
            files_to_process = all_analysis_files

        if not files_to_process:
            if selected_indices:
                print(f"No analysis files found matching the selection in '{self.output_folder}'. CSV not updated.")
            else:
                print(f"No analysis files (*_analysis.txt) found in '{self.output_folder}'. CSV not generated.")
            # Report this? Maybe not a failure if selection was intended.
            return True # Not necessarily a failure, just nothing to do.

        print(f"Processing {len(files_to_process)} analysis files for CSV output.")

        # --- Process selected/all files and update data ---
        processed_files_count = 0
        updated_rows = 0
        added_rows = 0

        # Sort files numerically based on link number for consistent order
        files_to_process.sort(key=lambda f: int(re.search(r'link(\d+)', f).group(1)) if re.search(r'link(\d+)', f) else 0)

        for file in files_to_process:
            # Extract product ID for reporting
            match = re.match(r'(link\d+)', file)
            product_id = match.group(1) if match else os.path.splitext(file)[0].replace('_analysis', '')
            # Note: Report start/pass/fail should happen in the calling function (gemini or main)
            # This function focuses on CSV generation.

            file_path = os.path.join(self.output_folder, file)
            print(f"Processing '{file}' for CSV...")

            parsed_data = self._parse_analysis_file(file_path, file)

            if parsed_data is None: # Critical parse failure
                print(f"  Skipping {file} due to critical parsing error.")
                report.fail_product(product_id, f"CSV: Critical parsing error for {file}") # Log failure in report
                continue # Skip to next file

            processed_files_count += 1
            link_url = parsed_data.get("Link", "").strip()

            if not link_url:
                print(f"  WARNING: No 'Link' URL found in parsed data for {file}. Cannot reliably update existing CSV row. Will try to append.")
                # Decide how to handle: append or skip? Appending might create duplicates if URL exists but wasn't parsed.
                # Let's append for now, user might need manual cleanup.
                self.existing_data.append(parsed_data)
                added_rows += 1
                report.pass_product(product_id, "CSV: Added (URL missing from analysis)") # Mark as passed but note issue
                continue

            # --- Update or Add Row ---
            if link_url in self.url_to_row_index:
                # Update existing row
                row_index = self.url_to_row_index[link_url]
                # Preserve any fields that might exist in CSV but not in expected_fields (unlikely with current setup)
                # Update only the fields defined in expected_fields
                for field in self.expected_fields:
                     if field in self.existing_data[row_index]: # Check if field exists in the row
                          self.existing_data[row_index][field] = parsed_data.get(field, "") # Update with parsed value or empty string
                     else: # Field was missing in original CSV row, add it
                          self.existing_data[row_index][field] = parsed_data.get(field, "")

                # Ensure all expected fields are present in the updated row
                for field in self.expected_fields:
                    if field not in self.existing_data[row_index]:
                         self.existing_data[row_index][field] = parsed_data.get(field, "") # Add missing field from parsed data

                print(f"  Updated existing row for URL: {link_url}")
                updated_rows += 1
                # report.pass_product(product_id, "CSV: Updated") # Don't overwrite potentially more specific status

            else:
                # Add new row
                # Ensure the new row dictionary only contains expected fields before adding
                new_row_data = {field: parsed_data.get(field, "") for field in self.expected_fields}
                self.existing_data.append(new_row_data)
                # Update the URL map for subsequent potential duplicates within this run (unlikely with sorting)
                self.url_to_row_index[link_url] = len(self.existing_data) - 1
                print(f"  Added new row for URL: {link_url}")
                added_rows += 1
                # report.pass_product(product_id, "CSV: Added") # Don't overwrite potentially more specific status


        # --- Write the final data back to CSV ---
        if processed_files_count == 0:
             print("No files were successfully processed to update the CSV.")
             return True # Still considered success as no errors occurred during the attempt


        try:
            print(f"\nWriting {len(self.existing_data)} rows to CSV: {self.csv_filename} ({updated_rows} updated, {added_rows} added)")
            # Create a backup of the old CSV before overwriting? Optional but safer.
            backup_filename = self.csv_filename + ".bak"
            if os.path.exists(self.csv_filename):
                 try:
                     shutil.copy2(self.csv_filename, backup_filename)
                     print(f"  Created backup: {backup_filename}")
                 except Exception as bk_err:
                      print(f"  Warning: Could not create CSV backup: {bk_err}")


            with open(self.csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile: # Use utf-8-sig for Excel compatibility
                # Use the expected_fields for the header order
                writer = csv.DictWriter(csvfile, fieldnames=self.expected_fields, extrasaction='ignore') # Ignore extra fields not in header
                writer.writeheader()
                writer.writerows(self.existing_data) # Write all rows (original + updated/added)

            print(f"Successfully updated/created CSV file: {self.csv_filename}")

            # --- Create timestamped copy in audit_report ---
            report_folder = os.path.join(self.output_folder, "audit_report")
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            selection_tag = f"_selection_{'_'.join(map(str, selected_indices))}" if selected_indices else ""
            csv_report_filename = f"audit_results{selection_tag}_{timestamp}.csv" # Use base name from constructor
            csv_report_path = os.path.join(report_folder, csv_report_filename)

            shutil.copy2(self.csv_filename, csv_report_path)
            print(f"CSV file also saved to: {csv_report_path}")

            return True # Overall success

        except Exception as e:
            print(f"Error writing CSV file '{self.csv_filename}': {str(e)}")
            report.fail_product("CSV Write Error", f"Failed to write CSV: {e}")
            # Restore backup?
            if os.path.exists(backup_filename):
                 try:
                     shutil.move(backup_filename, self.csv_filename)
                     print(f"  Restored CSV from backup: {backup_filename}")
                 except Exception as restore_err:
                      print(f"  FATAL: Could not restore CSV from backup: {restore_err}")
            return False


# Standalone function interface (wrapper around the class)
def add_csv_output(
    output_folder="output",
    csv_filename="audit_results.csv",
    links_file="links.txt",
    print_summary=False,
    selected_indices: Optional[List[int]] = None # Add selected_indices
):
    """
    Process analysis files and output/update a CSV file.

    Args:
        output_folder: Folder containing analysis text files
        csv_filename: Name of the output CSV file
        links_file: Path to the file containing product URLs (one per line)
        print_summary: Whether to print and save report summary at the end (handled by main now)
        selected_indices: List of 1-based link indices to process. If None, process all.

    Returns:
        bool: Whether processing was successful
    """
    # Import reporting utility
    from reporting_utils import report # Ensure report instance is available

    print(f"\n{'='*80}")
    print(f"GENERATING/UPDATING CSV FILE: {os.path.join(output_folder, csv_filename)}")
    if selected_indices:
        print(f"Processing selection: {selected_indices}")
    print(f"{'='*80}")

    try:
        processor = CsvProcessor(output_folder, csv_filename, links_file)
        success = processor.process_all_analyses(print_summary=False, selected_indices=selected_indices) # Pass selection

        # Summary printing is usually handled by main.py after all steps
        # if success and print_summary:
        #     report.print_summary()
        #     report.save_report(output_folder)

        return success
    except Exception as e:
         print(f"FATAL error during CSV processing setup or execution: {e}")
         report.fail_product("CSV Processing", f"Fatal error: {e}")
         return False