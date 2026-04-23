import os

countries = ['mx','pe','uy','co','cr','ec','hn','cl','bo','ar']
base = os.path.join('backend','app','countries')

for c in countries:
    path = os.path.join(base, c, 'config.py')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('max_amount=None', "max_amount=float('inf')")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed: {path}")
