import os
import json
from pypdf import PdfReader

docs_dir = '.'
results = {}

for f in os.listdir(docs_dir):
    if f.endswith('.pdf'):
        try:
            reader = PdfReader(os.path.join(docs_dir, f))
            text = ''
            if len(reader.pages) > 0:
                text = reader.pages[0].extract_text()[:300]
            results[f] = {'pages': len(reader.pages), 'preview': text.replace('\n', ' ')}
        except Exception as e:
            results[f] = {'error': str(e)}

print(json.dumps(results, indent=2))
