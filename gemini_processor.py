# c:\Users\wangx\Dropbox\Purdue\APEC Water\audit-automate\gemini_processor.py
import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import base64

# ... (GeminiProcessor class remains largely the same, _load_urls is fine) ...
# Make sure GeminiProcessor's _load_urls is called if needed, e.g. in __init__
class GeminiProcessor:
    """
    Process product data using Google's Gemini 2.5 Pro API.
    """

    def __init__(self, api_key: str):
        """
        Initialize the Gemini processor with API key.

        Args:
            api_key: Google API key for Gemini access
        """
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        # Consider making the model configurable or checking API limits
        try:
            # Use a specific, available model version
            self.model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17') # Changed to flash for potential cost/speed
            # You might want to add a check here to list models or confirm access
            print("Initialized Gemini Model: gemini-2.5-flash-preview-04-17")
        except Exception as model_init_error:
             print(f"FATAL: Failed to initialize Gemini model: {model_init_error}")
             print("Check API key, permissions, and available models.")
             # Re-raise or handle appropriately, maybe sys.exit(1)
             raise # Re-raise the exception to stop execution if model fails

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

        # Load URLs from links.txt if available
        self.url_map = self._load_urls()

    def _load_urls(self) -> Dict[str, str]:
        """Load URLs from links.txt file."""
        url_map = {}
        links_file = "links.txt"
        if os.path.exists(links_file):
            try:
                with open(links_file, 'r') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    url = line.strip()
                    if url:
                        url_map[f"link{i}"] = url
                print(f"Loaded {len(url_map)} URLs from {links_file}")
            except Exception as e:
                print(f"Error loading URLs from {links_file}: {str(e)}")
        else:
            print(f"Warning: {links_file} not found. URLs will not be included in analysis output (unless already present).")
        return url_map

    def _encode_image(self, image_path: str) -> str:
        """Encode an image file to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"Error: Image file not found for encoding: {image_path}")
            raise # Re-raise to be caught by the caller
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
             raise # Re-raise to be caught by the caller
        except Exception as e:
            print(f"Error reading text file {text_path}: {e}")
            raise

    def _format_direct_response(self, response_text: str, product_id: str) -> str:
        """
        Directly format the response without parsing.
        Ensures all expected fields are present, populating from response or defaults.
        """
        # Build a completely new response with all fields in the correct order
        result_lines = []
        # Use a case-insensitive regex search for flexibility
        field_values_from_response = {}
        # Find all **Field:** Value pairs
        pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*?)(?=\*\*[a-zA-Z0-9\s\+\?\#]+:\*\*|\Z)', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response_text)
        for match in matches:
             field_name = match[0].strip()
             field_value = match[1].strip()
             # Normalize the found field name for matching against expected_fields
             normalized_name = ' '.join(field_name.split()) # Handle potential extra spaces
             field_values_from_response[normalized_name] = field_value

        # Build the result with all fields in order, using found values or defaults
        for field in self.expected_fields:
            # Find the value from the response, attempting case-insensitive match
            value = ""
            found = False
            for response_field, response_value in field_values_from_response.items():
                 if response_field.lower() == field.lower():
                     value = response_value
                     found = True
                     break
            if not found:
                 # Handle missing fields - add default logic if needed, otherwise empty
                 # print(f"  Warning: Field '{field}' not found in Gemini response for {product_id}.") # Optional warning
                 value = "" # Default to empty if not found

            # Special handling for Link: Get from url_map if possible
            if field == "Link":
                url_from_map = self.url_map.get(product_id, "")
                # Prioritize URL from map if available, otherwise use response if present
                value = url_from_map if url_from_map else value

            result_lines.append(f"**{field}:** {value}")

        return "\n".join(result_lines)

    def process_product(self, image_path: str, text_path: str, prompt_path: str, product_id: str) -> str:
        """
        Process a product using the image, text, and prompt.

        Args:
            image_path: Path to the product image
            text_path: Path to the extracted text file
            prompt_path: Path to the prompt file
            product_id: Identifier for the product (e.g., "link1")

        Returns:
            Gemini's formatted analysis response or a fallback error response.
        """
        try:
            # Read the prompt
            prompt_text = self._read_text_file(prompt_path)

            # Read the extracted text
            product_text = self._read_text_file(text_path)

            # Encode the image to base64
            image_data = self._encode_image(image_path)

            # Prepare content parts for the API call
            content = [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{prompt_text}\n\nExtracted Text:\n{product_text}"},
                        {
                            "inline_data": {
                                "mime_type": "image/png", # Assuming PNG, might need check
                                "data": image_data,
                            }
                        },
                    ],
                }
            ]

            # Make the API call with safety settings and generation config
            # Adjust safety settings as needed. Blocking thresholds can be sensitive.
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            # Optional: Configure generation parameters (temp, top_k, etc.)
            # generation_config = genai.types.GenerationConfig(temperature=0.7)

            print(f"Calling Gemini API for {product_id}...")
            response = self.model.generate_content(
                content,
                safety_settings=safety_settings,
                # generation_config=generation_config # Uncomment if using config
            )
            # Check for response blocking or errors
            if not response.candidates:
                 raise ValueError(f"Gemini API call for {product_id} returned no candidates. Response: {response}")
            if response.candidates[0].finish_reason.name != "STOP":
                 print(f"Warning: Gemini response for {product_id} finished due to {response.candidates[0].finish_reason.name}, not 'STOP'.")
                 # Handle potentially incomplete response if needed

            response_text = response.text
            print(f"Response received from Gemini API for {product_id}")

            # Use the direct formatter, which is more robust
            formatted_response = self._format_direct_response(response_text, product_id)

            # Verify line count matches expected field count
            line_count = formatted_response.count('\n') + 1
            expected_count = len(self.expected_fields)
            print(f"Formatted response: {line_count} lines (expected: {expected_count})")

            if line_count != expected_count:
                print(f"WARNING: Line count ({line_count}) doesn't match expected field count ({expected_count}) for {product_id}!")
                # Log the raw response for debugging
                raw_response_path = text_path.replace('.txt', '_raw_gemini_response.txt')
                try:
                     with open(raw_response_path, 'w', encoding='utf-8') as rf:
                         rf.write(f"--- RAW GEMINI RESPONSE for {product_id} ---\n")
                         rf.write(response_text)
                         rf.write("\n\n--- FORMATTED RESPONSE (Issue Detected) ---\n")
                         rf.write(formatted_response)
                     print(f"Saved raw Gemini response for debugging to: {raw_response_path}")
                except Exception as log_err:
                     print(f"  Error saving raw response log: {log_err}")


            return formatted_response

        except FileNotFoundError as fnf_error:
             error_msg = f"Input file not found for {product_id}: {fnf_error}"
             print(f"ERROR: {error_msg}")
             # Create a fallback response with empty fields
             return self._create_fallback_response(product_id, error_msg)
        except Exception as e:
            error_msg = f"Error processing {product_id} with Gemini API: {str(e)}"
            print(f"ERROR: {error_msg}")
            # Create a fallback response with empty fields
            return self._create_fallback_response(product_id, error_msg)

    def _create_fallback_response(self, product_id: str, error_msg: str) -> str:
         """Creates a response string with all fields but empty values, noting the error."""
         fallback_lines = []
         for field in self.expected_fields:
             value = ""
             if field == "Link":
                 value = self.url_map.get(product_id, "") # Still try to add link
             # Optionally add the error message to a specific field or as a comment
             # For now, just return empty fields for consistency
             fallback_lines.append(f"**{field}:** {value}")
         # You could add a custom error field if needed:
         # fallback_lines.append(f"**Processing Error:** {error_msg}")
         print(f"Generated fallback (empty) analysis for {product_id} due to error.")
         return "\n".join(fallback_lines)


def process_all_products(
    output_folder: str,
    prompt_path: str,
    api_key: str,
    print_summary: bool = False,
    selected_indices: Optional[List[int]] = None # Add selected_indices
):
    """
    Process products in the output folder using Gemini.
    Optionally processes only selected products.

    Args:
        output_folder: Folder containing product screenshots and text files.
        prompt_path: Path to the prompt file.
        api_key: Google API key for Gemini access.
        print_summary: Whether to print and save report summary at the end.
        selected_indices: List of 1-based link indices to process. If None, process all.
    """
    # Import reporting utility
    from reporting_utils import report
    # import re # Already imported globally

    # Check if output folder exists
    if not os.path.exists(output_folder):
        print(f"Error: Output folder '{output_folder}' does not exist.")
        report.fail_product("Setup Error", f"Output folder '{output_folder}' not found.")
        return

    # Check if prompt file exists
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file '{prompt_path}' does not exist.")
        report.fail_product("Setup Error", f"Prompt file '{prompt_path}' not found.")
        return

    # Initialize the Gemini processor
    try:
        processor = GeminiProcessor(api_key)
    except Exception as e:
        print(f"Error initializing Gemini processor: {str(e)}")
        # Log a general failure if processor init fails
        report.fail_product("Gemini Init", f"Failed to initialize Gemini processor: {e}")
        return # Cannot proceed

    # --- Filter Files Based on Selection ---
    all_files = os.listdir(output_folder)
    product_files_to_process = [] # Store tuples of (product_id, png_file)

    if selected_indices:
        print(f"Gemini analysis selected for indices: {selected_indices}")
        for i in selected_indices:
            product_id = f"link{i}"
            png_file = f"{product_id}.png"
            txt_file = f"{product_id}.txt"
            png_path = os.path.join(output_folder, png_file)
            txt_path = os.path.join(output_folder, txt_file)

            if os.path.exists(png_path) and os.path.exists(txt_path):
                product_files_to_process.append((product_id, png_file))
            else:
                error_msg = f"Skipping {product_id}: Missing required file(s) ({png_file if not os.path.exists(png_path) else ''}{' and ' if not os.path.exists(png_path) and not os.path.exists(txt_path) else ''}{txt_file if not os.path.exists(txt_path) else ''})"
                print(f"WARNING: {error_msg}")
                report.start_product(product_id) # Start report to log failure
                report.fail_product(product_id, error_msg)
    else:
        # Process all found pairs if no selection
        print("Gemini analysis for all found products.")
        # Find all linkX.png files and assume corresponding linkX.txt exists
        potential_pngs = [f for f in all_files if re.match(r'link\d+\.png$', f) and not f.endswith('_cropped.png')]
        for png_file in sorted(potential_pngs):
             match = re.match(r'(link\d+)\.png$', png_file)
             if match:
                 product_id = match.group(1)
                 txt_file = f"{product_id}.txt"
                 if os.path.exists(os.path.join(output_folder, txt_file)):
                      product_files_to_process.append((product_id, png_file))
                 else:
                      print(f"WARNING: Skipping {product_id}: Text file '{txt_file}' not found.")
                      # Optionally report this failure
                      # report.start_product(product_id)
                      # report.fail_product(product_id, f"Text file '{txt_file}' not found.")


    if not product_files_to_process:
        if selected_indices:
             print(f"No valid PNG/TXT file pairs found for the selected indices in '{output_folder}'.")
        else:
             print(f"No valid PNG/TXT file pairs (linkX.png/linkX.txt) found in '{output_folder}'. Please run the capture step first.")
        return

    print(f"Found {len(product_files_to_process)} product(s) to analyze.")

    # Process each selected/found product
    for product_id, png_file in sorted(product_files_to_process, key=lambda item: int(re.search(r'\d+', item[0]).group())): # Sort numerically
        report.start_product(product_id) # Start reporting for this product

        # Construct the paths
        image_path = os.path.join(output_folder, png_file)
        text_path = image_path.replace('.png', '.txt')
        result_path = image_path.replace('.png', '_analysis.txt') # Analysis file path

        # Get URL from the processor's url_map (already loaded)
        url = processor.url_map.get(product_id, "")

        print(f"\n{'='*50}")
        print(f"Processing product: {product_id} ({png_file})")
        if url:
            print(f"URL (from links.txt): {url}")
        else:
            print(f"URL: Not found in {processor.links_file}") # Use attribute for filename
        print(f"{'='*50}")

        # Process the product using Gemini
        try:
            # Delete existing analysis file *before* calling Gemini to avoid partial writes on error
            if os.path.exists(result_path):
                try:
                    os.remove(result_path)
                    print(f"  Removed existing analysis file: {result_path}")
                except OSError as rm_err:
                     print(f"  Warning: Could not remove existing analysis file {result_path}: {rm_err}")


            result = processor.process_product(image_path, text_path, prompt_path, product_id)

            # Print the result summary (first few fields)
            print("\nGemini API Result Summary:")
            print(f"{'-'*30}")
            lines = result.split('\n')
            for i in range(min(5, len(lines))): # Print first 5 lines max
                print(lines[i])
            if len(lines) > 5:
                print("...")
            print(f"Total lines in analysis: {len(lines)}")
            print(f"{'-'*30}")

            # Write the result to a file
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"Analysis saved to: {result_path}")

            # Verify that the result has the correct number of fields (already checked in process_product)
            if len(lines) != len(processor.expected_fields):
                # Error already printed inside process_product
                error_msg = f"Output has wrong number of lines: {len(lines)} (expected {len(processor.expected_fields)})"
                report.fail_product(product_id, error_msg) # Mark as failed in report
            else:
                report.pass_product(product_id) # Mark as passed

        except Exception as e:
            # Catch errors from processor.process_product if it raises them instead of returning fallback
            error_msg = f"Critical error during Gemini processing for {product_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            report.fail_product(product_id, error_msg)
            # Ensure no partial analysis file exists if error happened *before* writing
            if os.path.exists(result_path):
                 try:
                     # Try to remove potentially corrupt/partial file
                     os.remove(result_path)
                 except OSError:
                      pass # Ignore if removal fails

    # Print the report summary only if requested (usually handled by main.py now)
    if print_summary:
        report.print_summary()
        report.save_report(output_folder)