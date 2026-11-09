"""Insert existing application screenshots into the README without duplicate sections."""
from pathlib import Path
from urllib.parse import quote
import re

root = Path(__file__).resolve().parents[1]
images = sorted(p for p in (root / 'screenshots').iterdir()
                if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}
                and p.name not in {'comparaison.png', 'histogrammes.png'})
if not images:
    print('Ajoutez vos captures dans screenshots, puis relancez cette commande.')
else:
    start, end = '<!-- application-screenshots:start -->', '<!-- application-screenshots:end -->'
    entries = ['## Captures de l’application', '']
    for index, path in enumerate(images, 1):
        entries.extend([f'![Interface de l’application — capture {index}](screenshots/{quote(path.name)})', ''])
    section = start + '\n' + '\n'.join(entries) + '\n' + end
    readme = root / 'README.md'
    text = readme.read_text(encoding='utf-8')
    if start in text and end in text:
        text = re.sub(re.escape(start) + r'.*?' + re.escape(end), lambda _: section, text, flags=re.S)
    else:
        text = text.replace('## Aperçu des résultats', section + '\n\n## Aperçu des résultats', 1)
    readme.write_text(text, encoding='utf-8')
    print(f'README mis à jour : {len(images)} captures.')
