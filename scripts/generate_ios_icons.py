#!/usr/bin/env python3
"""
iOS App Icon Generator for Menza
Generates all required icon sizes from a source image

Required: pip install Pillow

Usage: python generate_ios_icons.py [source_image.png]
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("❌ Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# iOS App Icon sizes required for App Store
IOS_ICON_SIZES = [
    # iPhone
    (20, 2),   # 20pt @2x = 40px
    (20, 3),   # 20pt @3x = 60px
    (29, 2),   # 29pt @2x = 58px
    (29, 3),   # 29pt @3x = 87px
    (40, 2),   # 40pt @2x = 80px
    (40, 3),   # 40pt @3x = 120px
    (60, 2),   # 60pt @2x = 120px
    (60, 3),   # 60pt @3x = 180px
    # iPad
    (20, 1),   # 20pt @1x = 20px
    (20, 2),   # 20pt @2x = 40px
    (29, 1),   # 29pt @1x = 29px
    (29, 2),   # 29pt @2x = 58px
    (40, 1),   # 40pt @1x = 40px
    (40, 2),   # 40pt @2x = 80px
    (76, 1),   # 76pt @1x = 76px
    (76, 2),   # 76pt @2x = 152px
    (83.5, 2), # 83.5pt @2x = 167px
    # App Store
    (1024, 1), # 1024pt @1x = 1024px
]

def create_menza_icon(size):
    """Create the Menza app icon programmatically"""
    # Create a new image with gradient background
    img = Image.new('RGB', (size, size), '#030306')
    draw = ImageDraw.Draw(img)
    
    # Create purple gradient background
    for y in range(size):
        # Gradient from dark purple to lighter purple
        ratio = y / size
        r = int(3 + (124 - 3) * ratio * 0.3)
        g = int(3 + (58 - 3) * ratio * 0.3)
        b = int(6 + (237 - 6) * ratio * 0.3)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    
    # Draw stylized "M" letter
    margin = size * 0.2
    m_width = size - (margin * 2)
    m_height = size * 0.5
    m_top = (size - m_height) / 2
    
    line_width = max(int(size * 0.08), 2)
    
    # M shape coordinates
    left = margin
    right = size - margin
    mid = size / 2
    top = m_top
    bottom = m_top + m_height
    peak = m_top + m_height * 0.35
    
    # Draw M with gradient purple
    purple = (168, 85, 247)  # #a855f7
    
    # Left vertical line
    draw.line([(left, bottom), (left, top)], fill=purple, width=line_width)
    # Left diagonal
    draw.line([(left, top), (mid, peak)], fill=purple, width=line_width)
    # Right diagonal
    draw.line([(mid, peak), (right, top)], fill=purple, width=line_width)
    # Right vertical line
    draw.line([(right, top), (right, bottom)], fill=purple, width=line_width)
    
    return img


def generate_icons(source_path=None, output_dir=None):
    """Generate all iOS icon sizes"""
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'ios' / 'App' / 'App' / 'Assets.xcassets' / 'AppIcon.appiconset'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load or create source image
    if source_path and os.path.exists(source_path):
        print(f"📷 Loading source image: {source_path}")
        source = Image.open(source_path)
        if source.mode != 'RGB':
            source = source.convert('RGB')
    else:
        print("🎨 Creating Menza icon programmatically...")
        source = create_menza_icon(1024)
    
    # Ensure source is large enough
    if source.size[0] < 1024:
        print(f"⚠️  Source image is {source.size[0]}px, upscaling to 1024px")
        source = source.resize((1024, 1024), Image.Resampling.LANCZOS)
    
    # Generate Contents.json
    contents = {
        "images": [],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }
    
    generated_sizes = set()
    
    for pt_size, scale in IOS_ICON_SIZES:
        px_size = int(pt_size * scale)
        
        # Skip duplicates
        if px_size in generated_sizes:
            continue
        generated_sizes.add(px_size)
        
        # Generate icon
        icon = source.resize((px_size, px_size), Image.Resampling.LANCZOS)
        
        # Filename
        if scale == 1:
            filename = f"Icon-{pt_size}.png"
        else:
            filename = f"Icon-{pt_size}@{scale}x.png"
        
        # Handle decimal point sizes
        if isinstance(pt_size, float):
            filename = filename.replace('.', '_')
        
        filepath = output_dir / filename
        icon.save(filepath, 'PNG')
        print(f"  ✅ Generated: {filename} ({px_size}x{px_size})")
        
        # Add to Contents.json
        size_str = f"{int(pt_size)}x{int(pt_size)}" if isinstance(pt_size, int) else f"{pt_size}x{pt_size}"
        contents["images"].append({
            "filename": filename,
            "idiom": "universal",
            "platform": "ios",
            "size": size_str
        })
    
    # Save the main 1024x1024 icon separately
    main_icon = source.resize((1024, 1024), Image.Resampling.LANCZOS)
    main_icon.save(output_dir / 'AppIcon-1024.png', 'PNG')
    print(f"  ✅ Generated: AppIcon-1024.png (1024x1024)")
    
    # Write Contents.json
    import json
    contents_path = output_dir / 'Contents.json'
    with open(contents_path, 'w') as f:
        json.dump(contents, f, indent=2)
    print(f"  ✅ Updated: Contents.json")
    
    print(f"\n🎉 Generated {len(generated_sizes)} icons in {output_dir}")
    return True


if __name__ == '__main__':
    source = sys.argv[1] if len(sys.argv) > 1 else None
    generate_icons(source)


