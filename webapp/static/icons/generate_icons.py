#!/usr/bin/env python3
"""
Generate PWA icons for Menza app.
Creates simple "M" logo icons in various sizes.
"""

import os

# SVG template for the Menza logo
SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7c3aed"/>
      <stop offset="100%" style="stop-color:#06b6d4"/>
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" rx="{radius}" fill="url(#bg)"/>
  <text x="50%" y="54%" 
        font-family="Arial, sans-serif" 
        font-size="{font_size}" 
        font-weight="bold" 
        fill="white" 
        text-anchor="middle" 
        dominant-baseline="middle">M</text>
</svg>'''

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def generate_icons():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for size in SIZES:
        radius = size // 5
        font_size = int(size * 0.6)
        
        svg_content = SVG_TEMPLATE.format(
            size=size,
            radius=radius,
            font_size=font_size
        )
        
        # Save as SVG (can be converted to PNG later)
        svg_path = os.path.join(script_dir, f'icon-{size}.svg')
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        print(f'Generated: icon-{size}.svg')

if __name__ == '__main__':
    generate_icons()
    print('\\nIcons generated! To convert to PNG, use:')
    print('  brew install librsvg')
    print('  for f in *.svg; do rsvg-convert -h ${f%.svg} $f > ${f%.svg}.png; done')

