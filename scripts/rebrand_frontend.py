import os

def replace_branding(directory):
    replacements = {
        'LatamTax': 'Declairo',
        'TaxFlow': 'Declairo',
        'latamtax': 'declairo',
        'taxflow': 'declairo',
        'LATAMTAX': 'DECLAIRO',
        'TAXFLOW': 'DECLAIRO',
        'Tax Flow': 'Declairo',
        'Latam Tax': 'Declairo'
    }
    
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(('.ts', '.tsx', '.css', '.html', '.json', '.md')):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    new_content = content
                    for old, new in replacements.items():
                        new_content = new_content.replace(old, new)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Updated: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    replace_branding(r'frontend\src')
    replace_branding(r'crypto-tax-landing-page')
