from PIL import Image

def crop_screenshot(output_filename):
    """
    Crop the screenshot to remove bottom 1/3.
    
    Args:
        output_filename: The filename of the image to crop
        
    Returns:
        bool: Whether the crop was successful
    """
    try:
        print("Cropping screenshot to remove bottom 1/3...")
        
        # Open the image
        img = Image.open(output_filename)
        
        # Get dimensions
        width, height = img.size
        
        # Calculate new height (2/3 of original)
        new_height = int(height * 2/3)
        
        # Crop the image (left, top, right, bottom)
        cropped_img = img.crop((0, 0, width, new_height))
        
        # Save over the original file
        cropped_img.save(output_filename)
        
        print(f"Screenshot cropped to remove bottom 1/3: {output_filename}")
        return True
    except Exception as crop_err:
        print(f"Error cropping screenshot: {crop_err}")
        return False