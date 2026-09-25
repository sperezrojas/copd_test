import os
import re

def tag_table_values(table_match):
    """
    Receives a matched <table>...</table> HTML string and applies styling tags
    to specific keywords inside the table, leaving other text untouched.
    """
    table_html = table_match.group(0)

    # Define a mapping of keywords to their CSS tag classes.
    # The order matters: more specific keywords should come first.
    tag_map = {
        # Keywords for the 'tag-hold' class (Red / Alert)
        "N/A": "tag-hold",
        "Not applicable": "tag-hold",

        # Keywords for the 'tag-warning' class (Yellow / Caution)
        "WEAKENED": "tag-warning",
        "INSUFFICIENT-EVIDENCE": "tag-warning",
        "FLAGGED": "tag-warning",
        "Inconclusive": "tag-warning",

        # Keywords for the 'tag' class (Green / Positive)
        "VERIFIED": "tag",
        "SUPPORTED": "tag"
    }

    # --- STEP 1: UNWRAP any existing tags at the start of a <td> to prevent nesting ---
    for keyword in tag_map:
        # This finds '<td...><span...>KEYWORD</span>' and replaces it with '<td...>KEYWORD'
        unwrap_pattern = rf'(<td[^>]*>)\s*<span class="tag[^"]*">\s*({keyword})\s*</span>'
        table_html = re.sub(unwrap_pattern, r'\1 \2', table_html, flags=re.IGNORECASE)

    # --- STEP 2: APPLY new, clean tags only if the keyword is at the start of the <td> ---
    for keyword, tag_class in tag_map.items():
        if keyword == "VERIFIED":
            # Special pattern for "VERIFIED": ensures it's not "Verified Date"
            pattern = rf'(<td[^>]*>)\s*(VERIFIED)\b(?!\s+Date)'
        else:
            # Standard pattern for all other keywords, anchored to the start of the <td>
            pattern = rf'(<td[^>]*>)\s*({keyword})\b'
        
        # The replacement wraps the keyword (group 2) in a span, keeping the original <td> (group 1)
        replacement = f'\\1<span class="{tag_class}">\\2</span>'
        table_html = re.sub(pattern, replacement, table_html, flags=re.IGNORECASE)

    return table_html

def clean_html_file(file_path):
    """
    Cleans and updates a single HTML file using standard library regex.
    """
    filename = os.path.basename(file_path)
    warning_triggered = False
    
    # 1. Parse chromosome and locus boundaries from filename (e.g., '4_2750001-3450000.html')
    locus_match = re.match(r'(\d+)_([\d,]+)-([\d,]+)\.html', filename)
    if not locus_match:
        print(f"⚠️ Skipping '{filename}': File name does not match expected pattern")
        return

    chromosome, start, end = locus_match.groups()
    start_clean = start.replace(',', '')
    end_clean = end.replace(',', '')
    
    locus_id = f"{chromosome}:{start_clean}-{end_clean}"
    chr_id = f"CHR{chromosome}"

    try:
        # Read file content safely
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 2. Isolate <div class="summary"> block
        nearest_gene = "unknown"
        summary_match = re.search(r'<div\s+class=["\']summary["\'][^>]*>(.*?)</div>', content, re.DOTALL | re.IGNORECASE)

        if summary_match:
            summary_content = summary_match.group(1)
            # Attempt to find the nearest gene within the summary content
            gene_patterns = [               
                #Format 1: (nearest gene GENE)
                r'\(\s*nearest\s+gene\s+([A-Za-z0-9\-_]+)',
                
                #Format 2: GENE (nearest gene...)
                r'([A-Za-z0-9\-_]+)\s+\(\s*nearest\s+gene',
                
                #Format 3: <strong>GENE</strong> (nearest gene...)
                r'<strong>([A-Za-z0-9\-_]+)</strong>\s+\(\s*nearest\s+gene',
                
                #Format 4: nearest gene: GENE
                r'nearest\s+gene(?:, pipeline annotation)?:?\s+([A-Za-z0-9\-_]+)',

                #Format 5: <strong>Nearest gene:</strong> GENE
                r'Nearest\s+gene:</strong>\s*([A-Za-z0-9\-_]+)',

                #Format 7: nearest: GENE
                r'nearest\s+=\s*([A-Za-z0-9\-_]+)',

                #Format 8: Nearest gene / FLAMES-prioritized: GENE
                r'Nearest\s+gene\s*/\s*FLAMES-prioritized:\s*([A-Za-z0-9\-_]+)',

                #Format 9: GENE (nearest...
                r'([A-Za-z0-9\-_]+)\s+\(\s*nearest',

                #Format 10: nearest gene = GENE
                r'nearest\s+gene\s*=\s*([A-Za-z0-9\-_]+)',

                #Format 11: <strong>Nearest gene (internal pipeline):</strong> GENE.
                r'<strong>Nearest\s+gene\s+\(internal pipeline\):</strong>\s*([A-Za-z0-9\-_]+)',

                #Format 12: Nearest/FLAMES-prioritized gene: GENE
                r'Nearest\s*/\s*FLAMES-prioritized\s+gene:\s*([A-Za-z0-9\-_]+)',

                #Format 13: nearest/MAGMA = GENE
                r'nearest\s*/\s*MAGMA\s*=\s*([A-Za-z0-9\-_]+)',

                #Format 14: nearest gene/FLAMES = GENE
                r'nearest\s+gene\s*/\s*FLAMES\s*=\s*([A-Za-z0-9\-_]+)',

                #Format 15: nearest gene/ABC-prioritized = GENE
                r'nearest\s+gene\s*/\s*ABC-prioritized\s*=\s*([A-Za-z0-9\-_]+)',

                #Format 16: GENE (sole candidate gene — nearest gene...
                r'([A-Za-z0-9\-_]+)\s+\(sole\s+candidate\s+gene\s+—\s+nearest\s+gene',

                #Format 17: GENE (nearest gene)
                r'([A-Za-z0-9\-_]+)\s+\(nearest\s+gene\)'
            ]
            
            for pattern in gene_patterns:
                gene_match = re.search(pattern, summary_content, re.IGNORECASE)
                if gene_match:
                    nearest_gene = gene_match.group(1)
                    break
        else:
            print(f"⚠️ Warning: Could not find <div class=\"summary\"> in '{filename}'.")

        # Check if we failed to find the gene, and print a clear warning if so
        if nearest_gene == "unknown":
            print(f"🚨 ALERT: Could not find nearest gene in '{filename}'! Check this file manually.")
            warning_triggered = True

        # Define the target title text
        target_title = f"Evidence Table - Locus {locus_id} (nearest gene {nearest_gene})"

        # 3. Update <title> and <h1> tags
        content = re.sub(r'<title[^>]*>.*?</title>', f'<title>{target_title}</title>', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<h1[^>]*>.*?</h1>', f'<h1>{target_title}</h1>', content, flags=re.DOTALL | re.IGNORECASE)

        # 4. Correctly set active navigation class
        # Remove active class from existing navigation link tags
        content = re.sub(r'class="nav-link\s+active"', 'class="nav-link"', content)
        content = re.sub(r"class='nav-link\s+active'", "class='nav-link'", content)
        
        # Add the active class to the correct chromosome link
        # Example target: <a class="nav-link" href=".../CHR4.html">CHR4</a> or similar
        # We find the link that matches CHR{chromosome} and ensure it has the active class
        nav_pattern = rf'(<a\s+[^>]*class=["\']nav-link)(["\'][^>]*>{chr_id}</a>)'
        content = re.sub(nav_pattern, r'\1 active\2', content, flags=re.IGNORECASE)

        # 5. Insert the "Return to CHR" Button
        # We place it right after the opening div of our main content wrapper
        # Checking if the button already exists to avoid duplicates
        button_html = f'<a href="../{chr_id}.html" class="return-button">&larr; Return to {chr_id} Overview</a>'

        # 6. Tag Values Inside Tables
        content = re.sub(r'<table[^>]*>.*?</table>', tag_table_values, content, flags=re.DOTALL | re.IGNORECASE)
        
        if "return-button" not in content:
            # Matches the <div id="main-content"> tag (allowing for classes or extra spacing)
            content = re.sub(
                r'(<div\s+[^>]*id=["\']main-content["\'][^>]*>)',
                rf'\1\n    {button_html}',
                content,
                flags=re.IGNORECASE
            )

        # Write modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Only print standard success if a gene was actually identified
        if not warning_triggered:
            print(f"✅ Successfully processed: {filename} -> [Gene: {nearest_gene}]")
        
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
        warning_triggered = True

    return warning_triggered

def batch_process_directory(directory="."):
    """
    Finds and processes all matching HTML template files in the target directory.
    """
    print("=" * 60)
    print(f"📂 Starting batch processing in: {os.path.abspath(directory)}")
    print("=" * 60)
    
    html_files = [f for f in os.listdir(directory) if f.endswith(".html")]
    processed_count = 0
    warnings_count = 0

    for filename in html_files:
        if re.match(r'^\d+_[\d,]+-[\d,]+\.html$', filename):
            file_path = os.path.join(directory, filename)

        # Run cleaning and check if it returned a warning flag
        is_warning = clean_html_file(file_path)
        
        if is_warning:
            warnings_count += 1
        processed_count += 1

    print("=" * 60)
    print(f"🎉 Batch processing complete!")
    print(f"📊 Total files updated: {processed_count}")
    if warnings_count > 0:
        print(f"🚨 Total manual review alerts: {warnings_count}")
    else:
        print("✨ Perfect run! No manual review alerts triggered.")
    print("=" * 60)

if __name__ == "__main__":
    # Runs in the current directory where the script is located
    batch_process_directory()
