import fitz
import os

for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.pdf'):
            p = os.path.join(root, f)
            doc = fitz.open(p)
            for page in doc:
                text = page.get_text()
                if 'audit_record' in text:
                    hits = [w for w in text.split() if 'audit_record' in w]
                    print(f"{p}: {hits}")
