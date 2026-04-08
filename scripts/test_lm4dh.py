import PyPDF2
reader = PyPDF2.PdfReader("/tmp/lm4dh.pdf")
text = ""
for p in reader.pages:
    text += p.extract_text() + "\n"

import re
for line in text.split("\n"):
    if "github" in line or "http" in line:
        print(line.strip())
