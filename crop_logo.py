#!/usr/bin/env python3
"""
Script to crop the play8 logo to remove excessive white space.
Detects content bounds and crops with minimal padding.
"""

from PIL import Image
import sys

def find_content_bounds(img, threshold=250):
    """
    Find the bounding box of non-white content.

    Args:
        img: PIL Image object
        threshold: RGB threshold (pixels below this are considered content)

    Returns:
        Tuple of (left, top, right, bottom) pixel coordinates
    """
    pixels = img.load()
    width, height = img.size

    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            if img.mode == 'RGBA':
                r, g, b, a = pixels[x, y]
            else:
                r, g, b = pixels[x, y]

            # If pixel is not white (below threshold)
            if r < threshold or g < threshold or b < threshold:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    return (min_x, min_y, max_x + 1, max_y + 1)

def crop_logo(input_path, output_path, padding=20):
    """
    Crop logo to content bounds with padding.

    Args:
        input_path: Path to input image
        output_path: Path to save cropped image
        padding: Pixels of padding to add around content
    """
    try:
        # Open image
        img = Image.open(input_path)

        print(f"Original image size: {img.width}x{img.height}")

        # Find content bounds
        left, top, right, bottom = find_content_bounds(img)

        print(f"Content bounds: left={left}, top={top}, right={right}, bottom={bottom}")
        print(f"Content size: {right-left}x{bottom-top}")

        # Add padding (ensure we don't go out of bounds)
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(img.width, right + padding)
        bottom = min(img.height, bottom + padding)

        print(f"With {padding}px padding: left={left}, top={top}, right={right}, bottom={bottom}")

        # Crop
        cropped = img.crop((left, top, right, bottom))

        print(f"Cropped size: {cropped.width}x{cropped.height}")

        # Save
        cropped.save(output_path, quality=95, optimize=True)

        print(f"\n✓ Cropped logo saved to: {output_path}")
        print(f"  Reduced from {img.width}x{img.height} to {cropped.width}x{cropped.height}")

        # Calculate reduction percentage
        original_pixels = img.width * img.height
        cropped_pixels = cropped.width * cropped.height
        reduction = ((original_pixels - cropped_pixels) / original_pixels) * 100
        print(f"  White space reduced by: {reduction:.1f}%")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    input_file = "play8-icon-white-bg.png"
    output_file = "play8-logo-cropped.png"

    print("Cropping logo to remove white space...\n")
    crop_logo(input_file, output_file, padding=20)
