import os
import re

def get_url_map(links_file="links.txt", output_folder="output"):
    """
    Create a mapping between link numbers and their URLs.
    
    Args:
        links_file: Path to the file containing links (one per line)
        output_folder: Folder containing the output files
        
    Returns:
        dict: Mapping from output file prefix to URL
    """
    url_map = {}
    
    # Check if links file exists
    if not os.path.exists(links_file):
        print(f"Warning: Links file '{links_file}' not found.")
        return url_map
    
    # Read links from file
    try:
        with open(links_file, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        
        # Create mapping from link number to URL
        for i, url in enumerate(links, 1):
            url_map[f"link{i}"] = url
        
        return url_map
    
    except Exception as e:
        print(f"Error reading links file: {str(e)}")
        return url_map

def update_analysis_files_with_urls(output_folder="output", links_file="links.txt"):
    """
    Update analysis files with URLs from the links file.
    
    Args:
        output_folder: Folder containing analysis text files
        links_file: Path to the file containing links (one per line)
    """
    # Get URL mapping
    url_map = get_url_map(links_file, output_folder)
    
    if not url_map:
        print("No URLs found in links file. Skipping URL updates.")
        return
    
    # Get all analysis text files
    analysis_files = [f for f in os.listdir(output_folder) if f.endswith('_analysis.txt')]
    
    if not analysis_files:
        print(f"No analysis files found in '{output_folder}'.")
        return
    
    # Track which URLs were used
    used_urls = set()
    
    # Process each analysis file
    for file in analysis_files:
        try:
            # Extract the link number prefix (e.g., "link1" from "link1_analysis.txt")
            match = re.match(r'(link\d+)_', file)
            if not match:
                print(f"Could not extract link number from {file}. Skipping.")
                continue
            
            link_prefix = match.group(1)
            
            # Get the URL for this link number
            url = url_map.get(link_prefix)
            if not url:
                print(f"No URL found for {link_prefix}. Skipping.")
                continue
                
            used_urls.add(link_prefix)
            
            file_path = os.path.join(output_folder, file)
            print(f"Updating {file} with URL...")
            
            # Read the content of the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace empty Link field with the URL
            updated_content = re.sub(r'\*\*Link:\*\*(\s*)(\n|$)', f'**Link:** {url}\\2', content)
            
            # Or replace an existing URL
            if updated_content == content:
                updated_content = re.sub(r'\*\*Link:\*\*(.*?)(\n|$)', f'**Link:** {url}\\2', content)
            
            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"  Updated {file} with URL: {url}")
        except Exception as e:
            print(f"Error updating {file}: {str(e)}. Skipping this file.")
            continue
    
    # Report any URLs that weren't used
    unused_urls = set(url_map.keys()) - used_urls
    if unused_urls:
        print(f"\nWARNING: The following links were not used (likely processing failed):")
        for link_key in sorted(unused_urls):
            print(f"  {link_key}: {url_map[link_key]}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update analysis files with URLs from links file")
    parser.add_argument("--folder", "-f", default="output", help="Folder containing analysis files (default: 'output')")
    parser.add_argument("--links", "-l", default="links.txt", help="Path to the links file (default: 'links.txt')")
    
    args = parser.parse_args()
    
    update_analysis_files_with_urls(args.folder, args.links)
    print("URL update complete!")