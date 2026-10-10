import glob

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Hex colors
    content = content.replace('"#111111"', '"#FAFAFA"')
    content = content.replace('fill="#181818"', 'fill="#EAEAEA"')
    content = content.replace('fill="#1a1a1a"', 'fill="#EAEAEA"')
    content = content.replace('fill="#0a0a0a"', 'fill="#FFFFFF"')
    content = content.replace('fill="#333333"', 'fill="#F0F0F0"')
    
    content = content.replace('outline="#ffffff"', 'outline="#333333"')
    content = content.replace('outline="#444444"', 'outline="#CCCCCC"')
    content = content.replace('outline="#555555"', 'outline="#BBBBBB"')
    
    content = content.replace('fill="#ffffff"', 'fill="#111111"')
    content = content.replace('fill="#eeeeee"', 'fill="#222222"')
    content = content.replace('fill="#dddddd"', 'fill="#333333"')
    content = content.replace('fill="#cccccc"', 'fill="#444444"')
    content = content.replace('fill="#bbbbbb"', 'fill="#555555"')
    content = content.replace('fill="#aaaaaa"', 'fill="#666666"')
    content = content.replace('fill="#999999"', 'fill="#777777"')
    
    # RGB colors for workflow
    content = content.replace('(18, 18, 18)', '(250, 250, 250)')
    content = content.replace('(30, 30, 30)', '(255, 255, 255)')
    content = content.replace('text_color = (255, 255, 255)', 'text_color = (20, 20, 20)')
    content = content.replace('(200, 200, 200)', '(60, 60, 60)')
    content = content.replace('(150, 150, 150)', '(100, 100, 100)')
    content = content.replace('(25, 25, 25)', '(240, 240, 240)')
    content = content.replace('outline=(100, 100, 100)', 'outline=(180, 180, 180)')

    # Sequence diagram specific adjustments
    content = content.replace('fill="#1e1e1e"', 'fill="#FFFFFF"')
    content = content.replace('fill="#2a2a2a"', 'fill="#F5F5F5"')
    
    # Fix potential double replace issue
    content = content.replace('text_color = (20, 20, 20)', 'text_color = (20, 20, 20)') # Identity

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for script in glob.glob("scripts/draw_*.py"):
    process_file(script)
    print(f"Processed {script}")
