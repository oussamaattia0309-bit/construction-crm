import re, zlib
path = r'C:\Users\USER\Desktop\stuff\web\CRM CAE\FACTURE 07-2026.pdf'
data = open(path, 'rb').read()
out = []
for m in re.finditer(rb'stream\r?\n(.*?)endstream', data, re.S):
    raw = m.group(1)
    try:
        d = zlib.decompress(raw)
    except Exception:
        d = raw
    for t in re.findall(rb'\(([^)]*)\)', d):
        try:
            out.append(t.decode('latin-1'))
        except Exception:
            pass
text = ' '.join(out)
open(r'C:\Users\USER\Desktop\stuff\web\CRM CAE\pdf_out.txt', 'w', encoding='utf-8').write(text)
print('done', len(text))
