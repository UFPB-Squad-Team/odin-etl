"""
Gera PDF bonito do documento de validação usando HTML + CSS + WeasyPrint.
"""
import markdown
from pathlib import Path
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "VALIDACAO_DADOS.md"
PDF_PATH = ROOT / "VALIDACAO_DADOS.pdf"

CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @top-center {
        content: "ODIN-ETL — Validação de Dados";
        font-size: 9px;
        color: #666;
        font-family: 'Inter', sans-serif;
    }
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9px;
        color: #666;
        font-family: 'Inter', sans-serif;
    }
}

:root {
    --primary: #1a365d;
    --accent: #2b6cb0;
    --success: #276749;
    --warning: #975a16;
    --danger: #9b2c2c;
    --bg-light: #f7fafc;
    --border: #e2e8f0;
    --text: #2d3748;
    --text-light: #4a5568;
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: var(--text);
    max-width: 100%;
}

h1 {
    font-size: 22pt;
    color: var(--primary);
    border-bottom: 3px solid var(--accent);
    padding-bottom: 12px;
    margin-top: 0;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}

h1 + blockquote {
    background: var(--bg-light);
    border-left: 4px solid var(--accent);
    padding: 12px 16px;
    margin: 0 0 24px 0;
    border-radius: 0 6px 6px 0;
}

h1 + blockquote p {
    margin: 4px 0;
    font-size: 9.5pt;
    color: var(--text-light);
}

h2 {
    font-size: 14pt;
    color: var(--primary);
    margin-top: 32px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1.5px solid var(--border);
    page-break-after: avoid;
}

h3 {
    font-size: 11.5pt;
    color: var(--accent);
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
}

h4 {
    font-size: 10.5pt;
    color: var(--text);
    font-weight: 600;
    margin-top: 16px;
    margin-bottom: 6px;
}

p {
    margin: 6px 0;
}

strong {
    color: var(--primary);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

thead {
    background: var(--primary);
    color: white;
}

th {
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

td {
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}

tr:nth-child(even) {
    background: var(--bg-light);
}

tr:hover {
    background: #edf2f7;
}

code {
    background: #edf2f7;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    color: var(--accent);
}

pre {
    background: #1a202c;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.5;
    margin: 12px 0;
    page-break-inside: avoid;
}

pre code {
    background: none;
    color: inherit;
    padding: 0;
    font-size: inherit;
}

blockquote {
    border-left: 4px solid var(--accent);
    margin: 12px 0;
    padding: 8px 16px;
    background: var(--bg-light);
    border-radius: 0 6px 6px 0;
}

blockquote p {
    margin: 4px 0;
    color: var(--text-light);
    font-style: italic;
}

hr {
    border: none;
    border-top: 2px solid var(--border);
    margin: 28px 0;
}

ul, ol {
    padding-left: 20px;
    margin: 8px 0;
}

li {
    margin: 4px 0;
}

/* Status badges via emoji */
em {
    font-style: normal;
}

/* Cover page styling */
h1:first-of-type {
    text-align: center;
    font-size: 26pt;
    margin-top: 60px;
    border-bottom: none;
    padding-bottom: 0;
}

/* Make the verdict table stand out */
h2 + table:first-of-type {
    border: 2px solid var(--accent);
    border-radius: 8px;
    overflow: hidden;
}
"""

def main():
    md_content = MD_PATH.read_text(encoding="utf-8")

    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "toc"],
    )

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    print("Gerando PDF...")
    HTML(string=full_html).write_pdf(str(PDF_PATH))
    size_mb = PDF_PATH.stat().st_size / 1_048_576
    print(f"PDF gerado: {PDF_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
