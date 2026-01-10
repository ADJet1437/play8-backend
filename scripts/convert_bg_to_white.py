#!/usr/bin/env python3
"""
Script to convert the background of play8-icon.PNG to pure white.
This will replace light-colored background pixels with pure white (#FFFFFF).
"""

from PIL import Image
import sys
import os

def convert_background_to_white(input_path, output_path, threshold=240):
    """
    Convert light background pixels to pure white.

    Args:
        input_path: Path to input image
        output_path: Path to save output image
        threshold: RGB value threshold (pixels above this become white)
    """
    try:
        # Open the image
        img = Image.open(input_path)

        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Get pixel data
        pixels = img.load()
        width, height = img.size

        # Process each pixel
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                # If pixel is light colored (close to white/gray background)
                # Replace with pure white
                if r >= threshold and g >= threshold and b >= threshold:
                    pixels[x, y] = (255, 255, 255, a)

        # Save the result
        img.save(output_path)
        print(f"✓ Successfully converted background to white")
        print(f"  Input:  {input_path}")
        print(f"  Output: {output_path}")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Get the parent directory (play8-backend) where images are stored
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    input_file = os.path.join(parent_dir, "play8-icon.png")
    output_file = os.path.join(parent_dir, "play8-icon-white-bg.png")

    print("Converting background to pure white...")
    convert_background_to_white(input_file, output_file)
