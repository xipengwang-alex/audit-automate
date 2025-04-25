# Audit Automation Tool

This tool automates the process of auditing product listings on retailer websites. It captures screenshots, extracts text, analyzes the content using Gemini AI, and outputs the results to a CSV file.

## Features

- Captures full-page screenshots of product pages
- Automatically finds and expands product details sections
- Extracts text content from the page
- Analyzes product listings using Google's Gemini 1.5 Pro API
- Outputs results in a consistent format to individual text files and a consolidated CSV file
- Provides tools to fix and standardize analysis files

## Prerequisites

- Python 3.6+
- Chrome browser
- Google API key for Gemini (required for AI analysis)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd audit-automate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### 1. Capturing Screenshots

Add product URLs to `links.txt`, one per line:

```
https://www.example.com/product1
https://www.example.com/product2
```

Run the screenshot capture:

```
python main.py
```

This will:
- Navigate to each URL
- Find and click on the product details section
- Take a full-page screenshot
- Extract the text content
- Save the screenshot and text to the `output` folder

### 2. Analyzing Products with Gemini

After capturing screenshots, run the Gemini analysis:

```
python main.py --gemini
```

This will:
- Process each product screenshot and text using Gemini AI
- Save the analysis results to individual text files in the `output` folder
- Generate a consolidated CSV file with all results

### 3. Creating/Updating the CSV File Only

If you want to generate or update the CSV file from existing analysis files:

```
python main.py --csv
```

### 4. Fixing Malformatted Analysis Files

If your analysis files don't follow the expected format, you can fix them:

```
python fix_and_convert.py
```

Options:
- `--folder/-f`: Specify the output folder (default: "output")
- `--csv-file/-c`: Specify the CSV filename (default: "audit_results.csv")
- `--fix-only`: Only fix the analysis files, don't create a CSV
- `--csv-only`: Only create a CSV file, don't fix the analysis files

### 5. Adding Missing URLs to Analysis Files

If your analysis files don't have URLs, you can add them from links.txt:

```
python link_extraction.py
```

Options:
- `--folder/-f`: Specify the output folder (default: "output")
- `--links/-l`: Specify the links file (default: "links.txt")

## Command Line Options

The main script accepts these arguments:

- `--input-file/-i`: Text file with product URLs (default: "links.txt")
- `--output-folder/-o`: Output folder for screenshots and text (default: "output")
- `--delay/-d`: Optional delay in seconds before starting
- `--retries/-r`: Number of retry attempts per link (default: 3)
- `--prompt-file/-p`: Path to the Gemini prompt file (default: "prompt.txt")
- `--gemini/-g`: Run Gemini analysis on existing files
- `--csv/-c`: Generate a CSV file from existing analysis files
- `--csv-file/-f`: Name of the output CSV file (default: "audit_results.csv")

## Output Format

The CSV file includes these fields:

- Link: Product URL
- Category: Product category
- SKU: Model number
- Retailer: Website name
- Images Count: Number of product images
- Images Visible Issues?: Yes/No
- Video Count: Number of product videos
- Video Visible Issues?: Yes/No
- A+ Content Type: Basic/None
- A+ Content Accuracy?: Yes/No/NA
- Title Actual: Product title text
- Title Accuracy?: Yes/No
- Bullet Point 1-9 Actual: Text for each bullet point
- Bullet Point 1-9 Accuracy?: Yes/No for each bullet
- Description Actual: Product description text
- Description Accuracy?: Yes/No

## Troubleshooting

- **Browser Detection Issues**: The script uses undetected-chromedriver to bypass anti-bot measures. If you encounter detection issues, try adding a delay with the `-d` option.

- **Missing Product Details**: If the script can't find the product details section, check if the website has a different structure and modify `details_finder.py` accordingly.

- **Gemini API Errors**: Check your API key and ensure you have access to the Gemini 1.5 Pro model.

- **Inconsistent CSV Format**: If the CSV format is inconsistent, run `fix_and_convert.py` to standardize the analysis files before generating the CSV.

## Customization

- **Modifying the Prompt**: Edit `prompt.txt` to change the instructions for Gemini AI.

- **Supporting Different Websites**: The current version is optimized for Home Depot. To support other websites, you may need to modify `details_finder.py` and `link_processor.py`.
