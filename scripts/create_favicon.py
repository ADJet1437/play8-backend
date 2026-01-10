#!/usr/bin/env python3
"""
Script to create a 32x32 square favicon from the transparent logo.
"""

from PIL import Image
import sys
import os

def create_favicon(input_path, output_path, size=32):
    """
    Create a square favicon by centering the logo on a transparent square canvas.

    Args:
        input_path: Path to input image
        output_path: Path to save output favicon
        size: Size of the square favicon (default 32x32)
    """
    try:
        # Open the image
        img = Image.open(input_path)

        # Ensure it has an alpha channel
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Calculate scaling to fit within the square while maintaining aspect ratio
        width, height = img.size
        aspect_ratio = width / height
        
        if aspect_ratio > 1:
            # Landscape: fit to width
            new_width = int(size * 0.9)  # Use 90% of size to add padding
            new_height = int(new_width / aspect_ratio)
        else:
            # Portrait: fit to height
            new_height = int(size * 0.9)  # Use 90% of size to add padding
            new_width = int(new_height * aspect_ratio)

        # Resize the image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create a new square image with transparent background
        favicon = Image.new('RGBA', (size, size), (0, 0, 0, 0))

        # Calculate position to center the resized image
        x_offset = (size - new_width) // 2
        y_offset = (size - new_height) // 2

        # Paste the resized image onto the square canvas
        favicon.paste(img_resized, (x_offset, y_offset), img_resized)

        # Save as PNG (favicon can be PNG or ICO)
        favicon.save(output_path, 'PNG')
        print(f"✓ Successfully created favicon")
        print(f"  Input:  {input_path}")
        print(f"  Output: {output_path}")
        print(f"  Size:   {size}x{size} pixels")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Get the parent directory (play8-backend) where images are stored
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    input_file = os.path.join(parent_dir, "play8-icon-transparent.png")
    output_file = os.path.join(parent_dir, "favicon.png")

    print("Creating 32x32 favicon...")
    create_favicon(input_file, output_file, size=32)

