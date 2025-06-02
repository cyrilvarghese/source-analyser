#!/usr/bin/env python3
import argparse
import pymupdf
import os
import json
from pathlib import Path

def extract_toc(input_path, output_path=None, format_type="json", show_info=False):
    """
    Extract table of contents from a document file.
    
    Args:
        input_path (str): Path to the input document file
        output_path (str, optional): Path to save the output file. If None, auto-generates JSON filename.
        format_type (str): Output format - 'text' or 'json' (default: json)
        show_info (bool): Whether to include document metadata
    """
    # Input validation
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Generate output path if not provided and format is JSON
    if output_path is None and format_type == "json":
        file_name = os.path.basename(input_path)
        file_base = os.path.splitext(file_name)[0]
        output_dir = os.path.dirname(input_path) or "."
        suffix = "_info" if show_info else "_toc"
        output_path = os.path.join(output_dir, f"{file_base}{suffix}.json")
    
    try:
        # Open document with PyMuPDF
        doc = pymupdf.open(input_path)
        
        # Extract TOC
        toc_raw = doc.get_toc()
        
        # Convert to standardized format
        toc_entries = []
        for entry in toc_raw:
            level = entry[0]
            title = entry[1]
            page_number = entry[2]
            
            toc_entries.append({
                'title': title.strip(),
                'level': level,
                'page_number': page_number
            })
        
        # Prepare output
        if show_info:
            doc_info = {
                'file_path': input_path,
                'page_count': doc.page_count,
                'is_pdf': doc.is_pdf,
                'is_encrypted': doc.is_encrypted,
                'metadata': doc.metadata or {},
                'toc_entries': toc_entries,
                'toc_count': len(toc_entries)
            }
            output_data = doc_info
        else:
            output_data = toc_entries
        
        # Format output
        if format_type == "json":
            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            if show_info:
                lines = [
                    f"Document: {os.path.basename(input_path)}",
                    f"Pages: {doc.page_count}",
                    f"TOC Entries: {len(toc_entries)}",
                    ""
                ]
                if doc.metadata:
                    lines.append("Metadata:")
                    for key, value in doc.metadata.items():
                        if value:
                            lines.append(f"  {key}: {value}")
                    lines.append("")
                
                lines.append("Table of Contents:")
                if toc_entries:
                    for entry in toc_entries:
                        indent = "  " * (entry['level'] - 1)
                        page_info = f" (Page: {entry['page_number']})" if entry['page_number'] else ""
                        lines.append(f"{indent}{entry['title']}{page_info}")
                else:
                    lines.append("  No table of contents found.")
                
                output_text = '\n'.join(lines)
            else:
                # Simple TOC format
                if toc_entries:
                    lines = []
                    for entry in toc_entries:
                        indent = "  " * (entry['level'] - 1)
                        page_info = f" (Page: {entry['page_number']})" if entry['page_number'] else ""
                        lines.append(f"{indent}{entry['title']}{page_info}")
                    output_text = '\n'.join(lines)
                else:
                    output_text = "No table of contents found."
        
        doc.close()
        
        # Output results
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"TOC extracted and saved to: {output_path}")
        else:
            print(output_text)
        
        if not output_path and toc_entries:
            print(f"\nFound {len(toc_entries)} TOC entries in '{os.path.basename(input_path)}'")
        
    except Exception as e:
        raise Exception(f"Error extracting TOC: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract table of contents from document files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python toc_extractor.py document.pdf
  python toc_extractor.py document.odt -f json
  python toc_extractor.py document.epub -o toc.txt
  python toc_extractor.py document.pdf -i -f json -o info.json
        """
    )
    
    parser.add_argument("input_file", help="Path to the input document file")
    parser.add_argument("-o", "--output", help="Path to save the output file (default: print to stdout)")
    parser.add_argument("-f", "--format", choices=["text", "json"], default="json", 
                       help="Output format (default: json)")
    parser.add_argument("-i", "--info", action="store_true", 
                       help="Include document metadata and info")
    
    args = parser.parse_args()
    
    try:
        extract_toc(args.input_file, args.output, args.format, args.info)
    except Exception as e:
        print(f"Error: {e}") 