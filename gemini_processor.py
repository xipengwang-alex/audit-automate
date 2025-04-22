import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import base64

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
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        
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
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image data
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _read_text_file(self, text_path: str) -> str:
        """
        Read content from a text file.
        
        Args:
            text_path: Path to the text file
            
        Returns:
            Content of the text file
        """
        with open(text_path, "r", encoding="utf-8") as text_file:
            return text_file.read()
    
    def _validate_and_fix_format(self, response_text: str) -> str:
        """
        Validate and fix the format of the Gemini response.
        
        Args:
            response_text: The text response from Gemini
            
        Returns:
            Corrected and formatted response text
        """
        # Check if all expected fields are present
        missing_fields = []
        for field in self.expected_fields:
            if f"**{field}:**" not in response_text:
                missing_fields.append(field)
        
        corrected_text = response_text
        
        # If fields are missing, add them at the end with empty values
        if missing_fields:
            print(f"Warning: {len(missing_fields)} fields are missing in the response. Adding empty fields...")
            for field in missing_fields:
                corrected_text += f"\n**{field}:**"
        
        # Ensure each field is on its own line and has the correct format
        formatted_lines = []
        
        # Use regex to find all field lines (including multiline values)
        pattern = r'\*\*(.*?):\*\*(.*?)(?=\*\*\w+:\*\*|$)'
        matches = re.findall(pattern, corrected_text, re.DOTALL)
        
        # Create a dictionary to store field values
        field_values = {}
        for match in matches:
            field_name = match[0].strip()
            field_value = match[1].strip()
            field_values[field_name] = field_value
        
        # Ensure all fields are present in the correct order
        for field in self.expected_fields:
            value = field_values.get(field, "")
            formatted_lines.append(f"**{field}:** {value}")
        
        # Join lines with newlines
        formatted_text = "\n".join(formatted_lines)
        
        return formatted_text
    
    def process_product(self, image_path: str, text_path: str, prompt_path: str, url: str = "") -> str:
        """
        Process a product using the image, text, and prompt.
        
        Args:
            image_path: Path to the product image
            text_path: Path to the extracted text file
            prompt_path: Path to the prompt file
            url: The product URL (optional)
            
        Returns:
            Gemini's response
        """
        # Read the prompt
        prompt_text = self._read_text_file(prompt_path)
        
        # Read the extracted text
        product_text = self._read_text_file(text_path)
        
        # Encode the image to base64
        image_data = self._encode_image(image_path)
        
        # Prepare content parts for the API call
        content = [
            {"role": "user", "parts": [
                {"text": f"{prompt_text}\n\nExtracted Text:\n{product_text}"},
                {"inline_data": {
                    "mime_type": "image/png",
                    "data": image_data
                }}
            ]}
        ]
        
        # Make the API call
        try:
            response = self.model.generate_content(content)
            response_text = response.text
            
            # Validate and fix the format
            formatted_response = self._validate_and_fix_format(response_text)
            
            # Add the URL to the response if provided
            if url and "**Link:**" in formatted_response:
                formatted_response = formatted_response.replace("**Link:**", f"**Link:** {url}")
            
            return formatted_response
        except Exception as e:
            error_msg = f"Error processing with Gemini API: {str(e)}"
            print(error_msg)
            
            # Create a fallback response with empty fields
            fallback_response = "\n".join([f"**{field}:**" for field in self.expected_fields])
            
            # Add the URL to the fallback response if provided
            if url and "**Link:**" in fallback_response:
                fallback_response = fallback_response.replace("**Link:**", f"**Link:** {url}")
                
            return fallback_response

def process_all_products(output_folder: str, prompt_path: str, api_key: str):
    """
    Process all products in the output folder.
    
    Args:
        output_folder: Folder containing the product screenshots and text files
        prompt_path: Path to the prompt file
        api_key: Google API key for Gemini access
    """
    # Import reporting utility
    from reporting_utils import report
    
    # Check if output folder exists
    if not os.path.exists(output_folder):
        print(f"Error: Output folder '{output_folder}' does not exist.")
        return
    
    # Check if prompt file exists
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file '{prompt_path}' does not exist.")
        return
    
    # Initialize the Gemini processor
    try:
        processor = GeminiProcessor(api_key)
    except Exception as e:
        print(f"Error initializing Gemini processor: {str(e)}")
        return
    
    # Get all PNG files in the output folder
    png_files = [f for f in os.listdir(output_folder) if f.endswith('.png') and not f.endswith('_cropped.png')]
    
    if not png_files:
        print(f"No PNG files found in '{output_folder}'. Please run the script without the -g flag first to capture screenshots.")
        return
    
    # Process each product
    for png_file in png_files:
        # Extract product ID (e.g., "link1" from "link1.png")
        match = re.match(r'(link\d+)', png_file)
        product_id = match.group(1) if match else os.path.splitext(png_file)[0]
        
        # Start product processing in report
        report.start_product(product_id)
        
        # Construct the paths
        image_path = os.path.join(output_folder, png_file)
        text_path = image_path.replace('.png', '.txt')
        
        # Check if text file exists
        if not os.path.exists(text_path):
            error_msg = f"Text file not found for {png_file}"
            print(f"WARNING: {error_msg}. Skipping.")
            report.fail_product(product_id, error_msg)
            continue
        
        # Try to extract the URL from the text file
        url = ""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                # Look for a URL pattern typically at the beginning of the text
                url_match = re.search(r'https?://[^\s]+', text_content)
                if url_match:
                    url = url_match.group(0)
        except Exception as e:
            print(f"Warning: Could not extract URL from text file: {str(e)}")
        
        print(f"\n{'='*50}")
        print(f"Processing product: {png_file}")
        if url:
            print(f"URL: {url}")
        print(f"{'='*50}")
        
        # Process the product
        try:
            result = processor.process_product(image_path, text_path, prompt_path, url)
            
            # Print the result
            print("\nGemini API Result:")
            print(f"{'-'*30}")
            print(result)
            print(f"{'-'*30}")
            
            # Save the result to a file
            result_path = image_path.replace('.png', '_analysis.txt')
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"Analysis saved to: {result_path}")
            
            # Check if all required fields are present in the result
            missing_fields = []
            for field in processor.expected_fields:
                if f"**{field}:**" not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Missing fields in analysis: {', '.join(missing_fields)}"
                print(f"WARNING: {error_msg}")
                report.fail_product(product_id, error_msg)
            else:
                report.pass_product(product_id)
                
        except Exception as e:
            error_msg = f"Error processing with Gemini API: {str(e)}"
            print(f"ERROR: {error_msg}")
            report.fail_product(product_id, error_msg)
    
    # Print the report summary
    report.print_summary()
    
    # Save the report to a file
    report.save_report(output_folder)