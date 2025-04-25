# audit-automate/csv_processor.py
import os
import csv
import re
import shutil
from datetime import datetime
from typing import List, Optional, Dict # Import typing helpers

class CsvProcessor:
    """
    Process Gemini analysis results and output to a consolidated CSV file.
    Uses links.txt to match product URLs with their corresponding output files (using base link ID).
    Supports updating existing CSV files selectively.
    """

    def __init__(self, output_folder, csv_filename="audit_results.csv", links_file="links.txt"):
        self.output_folder = output_folder
        self.csv_filename = os.path.join(output_folder, csv_filename)
        self.links_file = links_file
        self.url_map = self._load_urls_from_file()
        if not self.url_map:
             print("CSV Processor Warning: No URLs loaded. CSV 'Link' column might be incomplete.")

        self.expected_fields = [
            "Link", "Category", "SKU", "Retailer",
            "Images Count", "Images Visible Issues?",
            "Video Count", "Video Visible Issues?",
            "A+ Content Type", "A+ Content Accuracy?",
            "Title Actual", "Title Accuracy?",
        ]
        for i in range(1, 10):
            self.expected_fields.append(f"Bullet Point {i} Actual")
            self.expected_fields.append(f"Bullet Point {i} Accuracy?")
        self.expected_fields.extend([
            "Description Actual", "Description Accuracy?",
        ])

        self.existing_data = []
        self.url_to_row_index = {}

    def _load_urls_from_file(self) -> Dict[str, str]:
        """Load URLs from links.txt, mapping linkX to URL."""
        url_map = {}
        try:
            if not os.path.exists(self.links_file):
                print(f"Warning: Links file '{self.links_file}' not found during CSV init.")
                return url_map
            with open(self.links_file, 'r') as f: lines = f.readlines()
            for i, line in enumerate(lines, 1):
                url = line.strip()
                if url: url_map[f"link{i}"] = url
            print(f"CSV Processor: Loaded {len(url_map)} URLs from {self.links_file}")
            return url_map
        except Exception as e:
            print(f"Error loading URLs from {self.links_file} in CSV Processor: {str(e)}")
            return url_map

    def _load_existing_csv(self):
        """Loads data from the existing CSV file if it exists."""
        self.existing_data = []
        self.url_to_row_index = {}
        if not os.path.exists(self.csv_filename):
            print(f"CSV file '{self.csv_filename}' not found. Will create a new one.")
            return

        try:
            with open(self.csv_filename, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                # Handle potentially missing columns gracefully when loading
                loaded_fieldnames = reader.fieldnames or []
                processed_rows = []
                for row in reader:
                     # Ensure row has all expected fields, adding missing ones as empty strings
                     complete_row = {field: row.get(field, "") for field in self.expected_fields}
                     processed_rows.append(complete_row)

                self.existing_data = processed_rows
                print(f"Loaded {len(self.existing_data)} rows from existing CSV: {self.csv_filename}")

                # Map URL to row index
                for idx, row in enumerate(self.existing_data):
                    link = row.get("Link", "").strip()
                    if link:
                        self.url_to_row_index[link] = idx
        except Exception as e:
            print(f"Error reading existing CSV file '{self.csv_filename}': {str(e)}")
            print("Will proceed assuming an empty or new CSV.")
            self.existing_data = []
            self.url_to_row_index = {}

    def _parse_analysis_file(self, file_path: str, file_name: str) -> Optional[Dict[str, str]]:
        """
        Parse an analysis file (e.g., link1_homedepot_analysis.txt) and extract field values.
        Uses the base link ID (linkX) to set the Link field from url_map.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()

            parsed_data = {field: "" for field in self.expected_fields}

            # Extract base link ID (linkX) from file name
            match = re.match(r'(link\d+)_(\w+)_analysis\.txt$', file_name)
            base_product_id = match.group(1) if match else None # e.g., link1
            # retailer_name = match.group(2) if match else "Unknown"

            # Use regex to find **Field:** Value pairs
            pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*?)(?=\*\*[a-zA-Z0-9\s\+\?\#\(\)]+:\*\*|\Z)', re.DOTALL | re.IGNORECASE)
            matches = pattern.findall(content)

            found_values = {}
            for match_item in matches:
                 field_name_raw = match_item[0].strip()
                 field_value = match_item[1].strip()
                 normalized_name = ' '.join(field_name_raw.split())
                 found_values[normalized_name] = field_value

            # Populate parsed_data
            for field in self.expected_fields:
                value = ""
                found = False
                for found_field, found_val in found_values.items():
                    if re.sub(r'\s+', ' ', found_field).lower() == re.sub(r'\s+', ' ', field).lower():
                        value = found_val
                        found = True
                        break
                parsed_data[field] = value

            if base_product_id and base_product_id in self.url_map:
                parsed_data["Link"] = self.url_map[base_product_id]
                # print(f"  CSV Parser: Set Link for {base_product_id} from map.") # Debug
            elif not parsed_data.get("Link"):
                 # If Link wasn't in the analysis file AND not in map, log warning
                 print(f"  CSV Parser Warning: Could not determine Link for {file_name}.")
            # Retailer should already be correctly set by gemini_processor

            return parsed_data

        except FileNotFoundError:
             print(f"Error: Analysis file not found: {file_path}")
             return None
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            # Return fallback data with Link if possible
            empty_data = {field: "" for field in self.expected_fields}
            if base_product_id and base_product_id in self.url_map:
                empty_data["Link"] = self.url_map[base_product_id]
            # Try to extract retailer from filename as fallback
            if match:
                 retailer_name = match.group(2).capitalize()
                 if retailer_name == "Homedepot": retailer_name = "Home Depot"
                 empty_data["Retailer"] = retailer_name
            return empty_data

    def process_all_analyses(self, print_summary=False, selected_indices: Optional[List[int]] = None):
        """
        Process analysis files (e.g., link1_homedepot_analysis.txt) and output/update CSV.
        Handles selective updates based on selected_indices (matching link number).
        """
        from core.reporting_utils import report

        if not os.path.exists(self.output_folder):
            print(f"Error: Output folder '{self.output_folder}' does not exist.")
            report.fail_product("CSV Gen Error", f"Output folder '{self.output_folder}' does not exist.")
            return False

        self._load_existing_csv() # Load current CSV state

        # Regex to find analysis files like link1_homedepot_analysis.txt
        analysis_file_pattern = re.compile(r'(link\d+_(\w+))_analysis\.txt$')
        all_analysis_files = [f for f in os.listdir(self.output_folder) if analysis_file_pattern.match(f)]

        files_to_process = []
        processed_base_ids = set() # Track which base linkX have been processed

        if selected_indices:
            print(f"CSV Processing: Selecting analysis files for indices: {selected_indices}")
            selected_base_ids = {f"link{i}" for i in selected_indices}
            for f in all_analysis_files:
                match = analysis_file_pattern.match(f)
                if match:
                    base_id_match = re.match(r'(link\d+)', match.group(1))
                    if base_id_match:
                        base_id = base_id_match.group(1)
                        if base_id in selected_base_ids:
                            files_to_process.append(f)
                            processed_base_ids.add(base_id)

            missing_indices = set(selected_indices) - {int(re.search(r'\d+', bid).group()) for bid in processed_base_ids}
            if missing_indices:
                print(f"Warning: No analysis files found for selected indices: {sorted(list(missing_indices))}")

        else:
            print("CSV Processing: Processing all found analysis files.")
            files_to_process = all_analysis_files

        if not files_to_process:
            if selected_indices:
                 print(f"No analysis files found matching the selection in '{self.output_folder}'. CSV not updated.")
            else:
                 print(f"No analysis files (*_analysis.txt) found in '{self.output_folder}'. CSV not generated.")
            return True # Nothing to process

        print(f"Processing {len(files_to_process)} analysis files for CSV output.")

        processed_files_count = 0
        updated_rows = 0
        added_rows = 0

        # Sort files numerically based on link number
        files_to_process.sort(key=lambda f: int(re.search(r'link(\d+)', f).group(1)) if re.search(r'link(\d+)', f) else 0)

        for file in files_to_process:
            file_path = os.path.join(self.output_folder, file)
            print(f"Processing '{file}' for CSV...")

            parsed_data = self._parse_analysis_file(file_path, file)

            if parsed_data is None:
                print(f"  Skipping {file} due to critical parsing error.")
                # Reporting should be handled by the caller (main/gemini) based on analysis success
                continue

            processed_files_count += 1
            link_url = parsed_data.get("Link", "").strip()

            if not link_url:
                print(f"  WARNING: No 'Link' URL found in parsed data for {file}. Appending row, potential duplicate if URL exists in CSV already.")
                self.existing_data.append(parsed_data)
                added_rows += 1
                continue

            # Update or Add Row based on Link URL
            if link_url in self.url_to_row_index:
                row_index = self.url_to_row_index[link_url]
                for field in self.expected_fields:
                    if field in self.existing_data[row_index]:
                         self.existing_data[row_index][field] = parsed_data.get(field, self.existing_data[row_index][field]) # Update with parsed value or keep old if parse failed for field
                    else:
                         self.existing_data[row_index][field] = parsed_data.get(field, "")
                # Ensure all expected fields exist
                for field in self.expected_fields:
                    if field not in self.existing_data[row_index]:
                        self.existing_data[row_index][field] = parsed_data.get(field, "")
                print(f"  Updated existing row for URL: {link_url}")
                updated_rows += 1
            else:
                new_row_data = {field: parsed_data.get(field, "") for field in self.expected_fields}
                self.existing_data.append(new_row_data)
                self.url_to_row_index[link_url] = len(self.existing_data) - 1
                print(f"  Added new row for URL: {link_url}")
                added_rows += 1

        # Write the final data back to CSV
        if processed_files_count == 0:
             print("No files were successfully processed to update the CSV.")
             return True

        try:
            print(f"\nWriting {len(self.existing_data)} total rows to CSV: {self.csv_filename} ({updated_rows} updated, {added_rows} added based on this run)")
            backup_filename = self.csv_filename + ".bak"
            if os.path.exists(self.csv_filename):
                 try: shutil.copy2(self.csv_filename, backup_filename); print(f"  Created backup: {backup_filename}")
                 except Exception as bk_err: print(f"  Warning: Could not create CSV backup: {bk_err}")

            with open(self.csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.expected_fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.existing_data)

            print(f"Successfully updated/created CSV file: {self.csv_filename}")

            # Create timestamped copy in audit_report
            report_folder = os.path.join(self.output_folder, "audit_report")
            if not os.path.exists(report_folder): os.makedirs(report_folder)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_csv_name = os.path.splitext(os.path.basename(self.csv_filename))[0] # e.g., audit_results
            selection_tag = f"_selection_{'_'.join(map(str, selected_indices))}" if selected_indices else ""
            csv_report_filename = f"{base_csv_name}{selection_tag}_{timestamp}.csv"
            csv_report_path = os.path.join(report_folder, csv_report_filename)
            shutil.copy2(self.csv_filename, csv_report_path)
            print(f"CSV file also saved to: {csv_report_path}")

            return True
        except Exception as e:
            print(f"Error writing CSV file '{self.csv_filename}': {str(e)}")
            report.fail_product("CSV Write Error", f"Failed to write CSV: {e}")
            if os.path.exists(backup_filename):
                 try: shutil.move(backup_filename, self.csv_filename); print(f"  Restored CSV from backup: {backup_filename}")
                 except Exception as restore_err: print(f"  FATAL: Could not restore CSV from backup: {restore_err}")
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
    Process analysis files and output/update a CSV file. Now handles retailer suffixes in filenames.

    Args:
        output_folder: Folder containing analysis text files (e.g., link1_homedepot_analysis.txt)
        csv_filename: Name of the output CSV file
        links_file: Path to the file containing product URLs (one per line)
        print_summary: Whether to print and save report summary at the end (handled by main now)
        selected_indices: List of 1-based link indices to process. If None, process all.

    Returns:
        bool: Whether processing was successful
    """
    from core.reporting_utils import report

    print(f"\n{'='*80}")
    print(f"GENERATING/UPDATING CSV FILE: {os.path.join(output_folder, csv_filename)}")
    if selected_indices: print(f"Processing selection: {selected_indices}")
    print(f"{'='*80}")

    try:
        # Instantiate with the base CSV filename relative to the output folder
        processor = CsvProcessor(output_folder, os.path.basename(csv_filename), links_file)
        success = processor.process_all_analyses(print_summary=False, selected_indices=selected_indices)
        return success
    except Exception as e:
         print(f"FATAL error during CSV processing setup or execution: {e}")
         report.fail_product("CSV Processing", f"Fatal error: {e}")
         return False