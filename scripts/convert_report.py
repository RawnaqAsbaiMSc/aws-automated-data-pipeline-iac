import io
import os
from markdown import markdown
from html2docx import html2docx

in_md = os.path.join(os.path.dirname(__file__), '..', 'REPORT.md')
out_docx = os.path.join(os.path.dirname(__file__), '..', 'REPORT.docx')

with open(in_md, 'r', encoding='utf-8') as f:
    md = f.read()

html = markdown(md, extensions=['fenced_code', 'tables'])

# Convert HTML to DOCX
with open(out_docx, 'wb') as docx_file:
    html2docx(html, docx_file)

print('Wrote', out_docx)
