import os
import json
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
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
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
    
    def process_product(self, image_path: str, text_path: str, prompt_path: str) -> str:
        """
        Process a product using the image, text, and prompt.
        
        Args:
            image_path: Path to the product image
            text_path: Path to the extracted text file
            prompt_path: Path to the prompt file
            
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
            return response.text
        except Exception as e:
            return f"Error processing with Gemini API: {str(e)}"

def process_all_products(output_folder: str, prompt_path: str, api_key: str):
    """
    Process all products in the output folder.
    
    Args:
        output_folder: Folder containing the product screenshots and text files
        prompt_path: Path to the prompt file
        api_key: Google API key for Gemini access
    """
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
    png_files = [f for f in os.listdir(output_folder) if f.endswith('.png')]
    
    if not png_files:
        print(f"No PNG files found in '{output_folder}'. Please run the script without the -g flag first to capture screenshots.")
        return
    
    # Process each product
    for png_file in png_files:
        # Construct the paths
        image_path = os.path.join(output_folder, png_file)
        text_path = image_path.replace('.png', '.txt')
        
        # Check if text file exists
        if not os.path.exists(text_path):
            print(f"Warning: Text file not found for {png_file}. Skipping.")
            continue
        
        print(f"\n{'='*50}")
        print(f"Processing product: {png_file}")
        print(f"{'='*50}")
        
        # Process the product
        result = processor.process_product(image_path, text_path, prompt_path)
        
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