# core/gemini_processor.py
import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import base64
import sys

class GeminiProcessor:
    """
    Process product data using Google's Gemini 1.5 Pro API.
    Determines retailer from filename to select appropriate prompt.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.prompt_cache = {} # Cache for loaded prompts
        try:
            self.model = genai.GenerativeModel('models/gemini-1.5-flash-001')
            print(f"Initialized Gemini Model: {self.model.model_name}")
        except Exception as model_init_error:
             print(f"FATAL: Failed to initialize Gemini model: {model_init_error}")
             raise

        self.expected_fields = [
            "Link", "Category", "SKU", "Retailer", "Images Count",
            "Images Visible Issues?", "Video Count", "Video Visible Issues?",
            "A+ Content Type", "A+ Content Accuracy?", "Title Actual", "Title Accuracy?",
        ]
        for i in range(1, 10):
            self.expected_fields.extend([f"Bullet Point {i} Actual", f"Bullet Point {i} Accuracy?"])
        self.expected_fields.extend(["Description Actual", "Description Accuracy?"])

        self.url_map = self._load_urls()
        self.links_file_path = "links.txt"

    def _load_urls(self) -> Dict[str, str]:
        """Load URLs from links.txt file, mapping base link ID (linkX) to URL."""
        url_map = {}
        links_file = "links.txt"
        if os.path.exists(links_file):
            try:
                with open(links_file, 'r') as f: lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    url = line.strip()
                    if url: url_map[f"link{i}"] = url
                print(f"Gemini Processor: Loaded {len(url_map)} URLs from {links_file}")
            except Exception as e:
                print(f"Error loading URLs from {links_file}: {str(e)}")
        else:
            print(f"Warning: {links_file} not found. URLs will not be added automatically.")
        return url_map

    def _get_prompt(self, prompt_path: str) -> str:
        """Loads prompt from file and caches it."""
        if not os.path.exists(prompt_path):
             print(f"ERROR: Prompt file not found: {prompt_path}")
             raise FileNotFoundError(f"Required prompt file is missing: {prompt_path}")

        if prompt_path not in self.prompt_cache:
            print(f"Loading prompt from: {prompt_path}")
            self.prompt_cache[prompt_path] = self._read_text_file(prompt_path)
        return self.prompt_cache[prompt_path]

    def _encode_image(self, image_path: str) -> str:
        """Encode an image file to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"Error: Image file not found for encoding: {image_path}")
            raise
        except Exception as e:
             print(f"Error encoding image {image_path}: {e}")
             raise

    def _read_text_file(self, text_path: str) -> str:
        """Read content from a text file."""
        try:
            with open(text_path, "r", encoding="utf-8") as text_file:
                return text_file.read()
        except FileNotFoundError:
             print(f"Error: Text file not found for reading: {text_path}")
             raise
        except Exception as e:
            print(f"Error reading text file {text_path}: {e}")
            raise

    def _format_direct_response(self, response_text: str, product_id_with_retailer: str) -> str:
        """Formats response, ensuring all fields and correct Link/Retailer."""
        match = re.match(r'(link\d+)_(\w+)', product_id_with_retailer)
        base_product_id = match.group(1) if match else None
        retailer_name = match.group(2) if match else "Unknown"
        retailer_display_name = "Home Depot" if retailer_name.lower() == "homedepot" else retailer_name.capitalize()

        result_lines = []
        field_values_from_response = {}
        pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*?)(?=\*\*[a-zA-Z0-9\s\+\?\#\(\)]+:\*\*|\Z)', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response_text)
        for match_item in matches:
             field_name = match_item[0].strip()
             field_value = match_item[1].strip()
             normalized_name = ' '.join(field_name.split())
             field_values_from_response[normalized_name] = field_value

        for field in self.expected_fields:
            value = "" ; found = False
            for resp_field, resp_val in field_values_from_response.items():
                 if re.sub(r'\s+', ' ', resp_field).lower() == re.sub(r'\s+', ' ', field).lower():
                     value = resp_val ; found = True ; break
            if not found: value = ""

            if field == "Link": value = self.url_map.get(base_product_id, "") if base_product_id else ""
            elif field == "Retailer": value = retailer_display_name

            result_lines.append(f"**{field}:** {value}")
        return "\n".join(result_lines)

    def process_product(self, image_path: str, text_path: str, product_id_with_retailer: str) -> str:
        """
        Process a product using the image, text, and dynamically selected prompt.

        Args:
            image_path: Path to the product image
            text_path: Path to the extracted text file
            product_id_with_retailer: Identifier including retailer (e.g., "link1_homedepot")

        Returns:
            Gemini's formatted analysis response or a fallback error response.
        """
        match = re.match(r'(link\d+)_(\w+)', product_id_with_retailer)
        if not match:
             error_msg = f"Could not extract retailer from product ID: {product_id_with_retailer}"
             print(f"ERROR: {error_msg}")
             return self._create_fallback_response(product_id_with_retailer, error_msg)

        retailer_name = match.group(2).lower() # e.g., "homedepot", "lowes"
        prompt_path = f"prompts/prompt_{retailer_name}.txt"
        print(f"  Using prompt file: {prompt_path}")

        try:
            prompt_text = self._get_prompt(prompt_path) # Load/cache the correct prompt
            product_text = self._read_text_file(text_path)
            image_data = self._encode_image(image_path)

            content = [ # Content remains the same structure
                {"role": "user", "parts": [
                    {"text": f"{prompt_text}\n\nExtracted Text:\n{product_text}"},
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ]}
            ]
            safety_settings = [ # Safety settings remain the same
                {"category": c, "threshold": "BLOCK_NONE"} for c in [
                    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
                ]
            ]

            print(f"Calling Gemini API for {product_id_with_retailer}...")
            response = self.model.generate_content(content, safety_settings=safety_settings)

            try: response_text = response.text
            except Exception as resp_err:
                 print(f"  ERROR accessing response text: {resp_err}")
                 try:
                     response_text = "".join(part.text for part in response.parts) if response.parts else ""
                     if not response_text: raise ValueError("No text in parts.")
                 except Exception as parts_err:
                     raise ValueError(f"API call failed. No text. {parts_err}. Full Response: {response}")

            print(f"Response received from Gemini API for {product_id_with_retailer}")
            formatted_response = self._format_direct_response(response_text, product_id_with_retailer)

            # Verification and logging (remains the same)
            line_count = formatted_response.count('\n') + 1
            expected_count = len(self.expected_fields)
            print(f"Formatted response: {line_count} lines (expected: {expected_count})")
            if line_count != expected_count:
                print(f"WARNING: Line count mismatch for {product_id_with_retailer}!")
                raw_response_path = text_path.replace('.txt', '_raw_gemini_response.txt')
                try:
                     with open(raw_response_path, 'w', encoding='utf-8') as rf: rf.write(f"RAW:\n{response_text}\n\nFORMATTED:\n{formatted_response}")
                     print(f"Saved raw Gemini response to: {raw_response_path}")
                except Exception as log_err: print(f"  Error saving raw response log: {log_err}")

            return formatted_response

        except FileNotFoundError as fnf_error:
             error_msg = f"Input file not found for {product_id_with_retailer}: {fnf_error}"
             print(f"ERROR: {error_msg}")
             return self._create_fallback_response(product_id_with_retailer, error_msg)
        except Exception as e:
            error_msg = f"Error processing {product_id_with_retailer} with Gemini API: {str(e)}"
            print(f"ERROR: {error_msg}")
            return self._create_fallback_response(product_id_with_retailer, error_msg)

    def _create_fallback_response(self, product_id_with_retailer: str, error_msg: str) -> str:
         """Creates a response string with empty fields, noting the error."""
         match = re.match(r'(link\d+)_(\w+)', product_id_with_retailer)
         base_product_id = match.group(1) if match else None
         retailer_name = match.group(2) if match else "Unknown"
         retailer_display_name = "Home Depot" if retailer_name.lower() == "homedepot" else retailer_name.capitalize()

         fallback_lines = []
         for field in self.expected_fields:
             value = ""
             if field == "Link" and base_product_id: value = self.url_map.get(base_product_id, "")
             elif field == "Retailer": value = retailer_display_name
             elif field == "Description Actual": value = f"ERROR PROCESSING: {error_msg}"

             fallback_lines.append(f"**{field}:** {value}")
         print(f"Generated fallback analysis for {product_id_with_retailer} due to error: {error_msg}")
         return "\n".join(fallback_lines)

def process_all_products(
    output_folder: str,
    api_key: str,
    print_summary: bool = False,
    selected_indices: Optional[List[int]] = None
):
    """
    Process products in the output folder using Gemini.
    Determines retailer from filename to select appropriate prompt.
    """
    from core.reporting_utils import report

    if not os.path.exists(output_folder):
        print(f"Error: Output folder '{output_folder}' does not exist.")
        report.fail_product("Setup Error", f"Output folder '{output_folder}' not found.")
        return

    try:
        processor = GeminiProcessor(api_key)
    except Exception as e:
        print(f"Error initializing Gemini processor: {str(e)}")
        report.fail_product("Gemini Init", f"Failed to initialize Gemini processor: {e}")
        return

    all_files = os.listdir(output_folder)
    product_files_to_process = [] # Store tuples of (product_id_with_retailer, png_file)
    file_pattern = re.compile(r'(link\d+_(\w+))\.png$') # Matches linkX_retailer.png

    if selected_indices:
        print(f"Gemini analysis selected for indices: {selected_indices}")
        found_files_for_selection = []
        processed_indices = set()
        for f in all_files:
            match = file_pattern.match(f)
            if match:
                product_id_with_retailer = match.group(1)
                base_id_match = re.match(r'link(\d+)', product_id_with_retailer)
                if base_id_match:
                    link_index = int(base_id_match.group(1))
                    if link_index in selected_indices:
                        txt_file = f"{product_id_with_retailer}.txt"
                        if os.path.exists(os.path.join(output_folder, txt_file)):
                             found_files_for_selection.append((product_id_with_retailer, f))
                             processed_indices.add(link_index)
                        else:
                             msg=f"Text file '{txt_file}' not found."
                             print(f"WARNING: Skipping {product_id_with_retailer} (selected): {msg}")
                             report.start_product(product_id_with_retailer)
                             report.fail_product(product_id_with_retailer, msg)
        product_files_to_process = found_files_for_selection
        missing_indices = set(selected_indices) - processed_indices
        if missing_indices:
            print(f"Warning: No valid PNG/TXT files found for selected indices: {sorted(list(missing_indices))}")
            for idx in sorted(list(missing_indices)):
                 report.start_product(f"link{idx}_selected_missing")
                 report.fail_product(f"link{idx}_selected_missing", f"No valid PNG/TXT files for index {idx}")
    else:
        print("Gemini analysis for all found retailer-specific products.")
        for f in all_files:
            match = file_pattern.match(f)
            if match:
                 product_id_with_retailer = match.group(1)
                 txt_file = f"{product_id_with_retailer}.txt"
                 if os.path.exists(os.path.join(output_folder, txt_file)):
                      product_files_to_process.append((product_id_with_retailer, f))
                 else:
                      print(f"WARNING: Skipping {product_id_with_retailer}: Text file '{txt_file}' not found.")

    if not product_files_to_process:
        print(f"No valid retailer-specific PNG/TXT file pairs found in '{output_folder}' to process.")
        return

    print(f"Found {len(product_files_to_process)} product(s) to analyze.")
    product_files_to_process.sort(key=lambda item: int(re.search(r'link(\d+)', item[0]).group(1)) if re.search(r'link(\d+)', item[0]) else 0)

    for product_id_with_retailer, png_file in product_files_to_process:
        report.start_product(product_id_with_retailer)

        image_path = os.path.join(output_folder, png_file)
        text_path = image_path.replace('.png', '.txt')
        result_path = image_path.replace('.png', '_analysis.txt')

        # Base ID and URL for logging
        base_id_match = re.match(r'(link\d+)', product_id_with_retailer)
        base_product_id = base_id_match.group(1) if base_id_match else None
        url = processor.url_map.get(base_product_id, "") if base_product_id else ""

        print(f"\n{'='*50}")
        print(f"Processing product: {product_id_with_retailer} ({png_file})")
        if url: print(f"URL (from links.txt for {base_product_id}): {url}")
        else: print(f"URL: Not found in {processor.links_file_path} for {base_product_id}")
        print(f"{'='*50}")

        try:
            if os.path.exists(result_path):
                try: os.remove(result_path); print(f"  Removed existing analysis file: {result_path}")
                except OSError as rm_err: print(f"  Warning: Could not remove analysis file {result_path}: {rm_err}")

            # Call process_product - it now determines the prompt itself
            result = processor.process_product(image_path, text_path, product_id_with_retailer)

            print("\nGemini API Result Summary:")
            print(f"{'-'*30}")
            lines = result.split('\n')
            for i in range(min(5, len(lines))): print(lines[i])
            if len(lines) > 5: print("...")
            print(f"Total lines in analysis: {len(lines)}")
            print(f"{'-'*30}")

            with open(result_path, 'w', encoding='utf-8') as f: f.write(result)
            print(f"Analysis saved to: {result_path}")

            if len(lines) != len(processor.expected_fields):
                error_msg = f"Output line count mismatch: {len(lines)} (expected {len(processor.expected_fields)})"
                report.fail_product(product_id_with_retailer, error_msg)
            else:
                report.pass_product(product_id_with_retailer)

        except Exception as e:
            error_msg = f"Critical error during Gemini processing for {product_id_with_retailer}: {str(e)}"
            print(f"ERROR: {error_msg}")
            report.fail_product(product_id_with_retailer, error_msg)
            if os.path.exists(result_path):
                 try: os.remove(result_path)
                 except OSError: pass
