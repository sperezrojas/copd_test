import os
import re
import tempfile
from bs4 import BeautifulSoup

# Master template using native placeholders
MASTER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__PAGE_TITLE__</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <div id="sidebar">
        <div class="sidebar-header">
            🧬 Agentic Gene Prioritization<br>Dashboard
        </div>

        <div class="sidebar-section">
            <div class="sidebar-title">Overview</div>
            <a class="nav-link" href="../index.html">🏠 Home</a>
            <a class="nav-link" href="../methods.html">🔬 Methods</a>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-title">Chromosomes</div>
            <a class="nav-link active" href="../CHR1.html">CHR1</a>
            <a class="nav-link" href="../CHR2.html">CHR2</a>
            <a class="nav-link" href="../CHR3.html">CHR3</a>
            <a class="nav-link" href="../CHR4.html">CHR4</a>
            <a class="nav-link" href="../CHR5.html">CHR5</a>
            <a class="nav-link" href="../CHR6.html">CHR6</a>
            <a class="nav-link" href="../CHR7.html">CHR7</a>
            <a class="nav-link" href="../CHR8.html">CHR8</a>
            <a class="nav-link" href="../CHR9.html">CHR9</a>
            <a class="nav-link" href="../CHR10.html">CHR10</a>
            <a class="nav-link" href="../CHR11.html">CHR11</a>
            <a class="nav-link" href="../CHR12.html">CHR12</a>
            <a class="nav-link" href="../CHR13.html">CHR13</a>
            <a class="nav-link" href="../CHR14.html">CHR14</a>
            <a class="nav-link" href="../CHR15.html">CHR15</a>
            <a class="nav-link" href="../CHR16.html">CHR16</a>
            <a class="nav-link" href="../CHR17.html">CHR17</a>
            <a class="nav-link" href="../CHR18.html">CHR18</a>
            <a class="nav-link" href="../CHR19.html">CHR19</a>
            <a class="nav-link" href="../CHR20.html">CHR20</a>
            <a class="nav-link" href="../CHR21.html">CHR21</a>
            <a class="nav-link" href="../CHR22.html">CHR22</a>
        </div>
    </div>

    <div id="main-content">
        <div class="content-card">
            __CORE_CONTENT__
        </div>
    </div>
</body>
</html>
"""

def clean_verdict_tags(soup):
    for td in soup.find_all("td"):
        text = td.get_text()
        if "WEAKENED" in text and "<span" not in str(td):
            td.string = ""
            new_tag = soup.new_tag("span", **{"class": "tag-warning"})
            new_tag.string = "WEAKENED"
            td.append(new_tag)
            td.append(text.replace("WEAKENED", ""))
        elif "CONTESTED" in text and "<span" not in str(td):
            td.string = ""
            new_tag = soup.new_tag("span", **{"class": "tag-warning"})
            new_tag.string = "CONTESTED"
            td.append(new_tag)
            td.append(text.replace("CONTESTED", ""))
        elif "HOLDS" in text and "<span" not in str(td):
            td.string = ""
            new_tag = soup.new_tag("span", **{"class": "tag-hold"})
            new_tag.string = "HOLDS"
            td.append(new_tag)
            td.append(text.replace("HOLDS", ""))
        elif "Verified" in text and "<span" not in str(td):
            td.string = ""
            new_tag = soup.new_tag("span", **{"class": "tag"})
            new_tag.string = "Verified"
            td.append(new_tag)
            td.append(text.replace("Verified", ""))

def process_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for element in soup(["style", "script", "meta", "link"]):
        element.decompose()

    body = soup.find("body")
    if not body:
        return "", "Untitled"

    h1 = body.find("h1")
    page_title = "Evidence Table"
    if h1:
        raw_title = h1.get_text().strip()
        locus_match = re.search(r'(\d+[\:_]\d+[\-_]\d+)', raw_title)
        if locus_match:
            formatted_locus = locus_match.group(1).replace('_', ':')
            h1.string = f"Evidence Table — Locus {formatted_locus}"
            page_title = f"Evidence Table — {formatted_locus}"
        else:
            h1.string = raw_title
            page_title = raw_title

    summary_paragraphs = []
    first_table = body.find("table")
    
    for element in list(body.children):
        if element == first_table:
            break
        if element.name == "p":
            summary_paragraphs.append(element)

    if summary_paragraphs:
        summary_div = soup.new_tag("div", attrs={"class": "summary"})
        for p in summary_paragraphs:
            summary_div.append(p.extract())
        if h1:
            h1.insert_after(summary_div)

    for table in body.find_all("table"):
        table["class"] = "evidence-table"
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if cells:
                cells[0]["class"] = "gene"

        wrapper = soup.new_tag("div", attrs={"class": "evidence-table-wrapper"})
        table.wrap(wrapper)

    clean_verdict_tags(soup)

    for tag in body.find_all(True):
        if "style" in tag.attrs:
            del tag.attrs["style"]

    core_content = body.encode_contents().decode("utf-8")
    return core_content, page_title

def main():
    # Gets the directory where convert_all.py is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_dir = os.path.join(script_dir, "messy_html")
    output_dir = os.path.join(script_dir, "clean_html")

    if not os.path.exists(input_dir):
        print(f"Error: Could not find folder '{input_dir}'. Please ensure 'messy_html' is in the same folder as this script.")
        return

    os.makedirs(output_dir, exist_ok=True)

    file_count = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".html"):
            input_path = os.path.join(input_dir, filename)
            core_content, page_title = process_html_file(input_path)
            
            clean_html = MASTER_TEMPLATE.replace("__PAGE_TITLE__", page_title).replace("__CORE_CONTENT__", core_content)
            
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(clean_html)
            
            file_count += 1

    print(f"Successfully converted {file_count} files into '{output_dir}'")

if __name__ == "__main__":
    main()