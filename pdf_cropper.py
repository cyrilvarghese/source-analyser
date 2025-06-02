import argparse
from PyPDF2 import PdfReader, PdfWriter
import os

def crop_pdf(input_path, output_path=None, start_page=1, end_page=None):
    """
    Extract pages from a PDF within the specified range (inclusive).
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str, optional): Path to save the output PDF file. If None, will generate automatically.
        start_page (int): Starting page number (1-indexed)
        end_page (int, optional): Ending page number (1-indexed). If None, uses the last page.
    """
    # Input validation
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Generate output path if not provided
    if output_path is None:
        file_name = os.path.basename(input_path)
        file_base = os.path.splitext(file_name)[0]
        output_dir = os.path.dirname(input_path)
        output_path = os.path.join(output_dir, f"{file_base}_cropped.pdf")
    
    if start_page < 1:
        raise ValueError("Start page must be at least 1")
    
    try:
        # Read the input PDF
        pdf_reader = PdfReader(input_path)
        
        # Validate page range
        total_pages = len(pdf_reader.pages)
        
        # If end_page not specified, use the last page
        if end_page is None:
            end_page = total_pages
            
        if start_page > total_pages:
            raise ValueError(f"Start page exceeds PDF length ({total_pages} pages)")
        if end_page > total_pages:
            print(f"Warning: End page {end_page} exceeds document length. Using last page ({total_pages}) instead.")
            end_page = total_pages
        
        # Create a new PDF with selected pages
        pdf_writer = PdfWriter()
        for page_num in range(start_page - 1, end_page):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Write the output to a file
        with open(output_path, "wb") as output_file:
            pdf_writer.write(output_file)
        
        print(f"Successfully extracted pages {start_page} to {end_page} from '{input_path}' to '{output_path}'")
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract pages from a PDF file")
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("-o", "--output_pdf", help="Path to save the output PDF file (default: inputname_cropped.pdf)")
    parser.add_argument("-s", "--start_page", type=int, default=1, help="Starting page number (1-indexed, default: 1)")
    parser.add_argument("-e", "--end_page", type=int, help="Ending page number (1-indexed, default: last page)")
    
    args = parser.parse_args()
    
    try:
        crop_pdf(args.input_pdf, args.output_pdf, args.start_page, args.end_page)
    except Exception as e:
        print(f"Error: {e}")
