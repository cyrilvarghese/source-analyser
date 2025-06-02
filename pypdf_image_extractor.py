import logging
import time
from pathlib import Path
import argparse
import sys

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("Error: Neither pypdf nor PyPDF2 is installed.")
        print("Please install pypdf with: pip install pypdf")
        sys.exit(1)

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL/Pillow not installed. Some image processing features will be limited.")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_log = logging.getLogger(__name__)

def save_image_with_fallbacks(image_data, filename, image_name="unknown"):
    """
    Try multiple methods to save an image, handling different formats and color spaces.
    """
    saved = False
    
    # Method 1: Save raw data as-is
    try:
        with open(filename, "wb") as fp:
            fp.write(image_data)
        _log.info(f"Saved raw image: {filename}")
        saved = True
        
        # If PIL is available, try to improve the image
        if PIL_AVAILABLE:
            try:
                # Try to open and convert the image
                with Image.open(filename) as img:
                    # Convert to RGB if not already
                    if img.mode not in ('RGB', 'RGBA'):
                        if img.mode == 'CMYK':
                            # Convert CMYK to RGB
                            img = img.convert('RGB')
                            _log.info(f"Converted CMYK to RGB: {filename}")
                        elif img.mode == 'L':
                            # Grayscale to RGB
                            img = img.convert('RGB')
                            _log.info(f"Converted grayscale to RGB: {filename}")
                        elif img.mode == '1':
                            # 1-bit to RGB
                            img = img.convert('RGB')
                            _log.info(f"Converted 1-bit to RGB: {filename}")
                        else:
                            # Try generic conversion
                            img = img.convert('RGB')
                            _log.info(f"Converted {img.mode} to RGB: {filename}")
                    
                    # Auto-orient the image
                    img = ImageOps.exif_transpose(img)
                    
                    # Save the improved version
                    improved_filename = filename.with_suffix('.improved.png')
                    img.save(improved_filename, 'PNG', optimize=True)
                    _log.info(f"Saved improved image: {improved_filename}")
                    
            except Exception as e:
                _log.debug(f"Could not improve image {filename}: {e}")
                
    except Exception as e:
        _log.warning(f"Could not save raw image {filename}: {e}")
    
    # Method 2: Try different extensions if raw save failed
    if not saved:
        for ext in ['.jpg', '.jpeg', '.bmp', '.tiff']:
            try:
                alt_filename = filename.with_suffix(ext)
                with open(alt_filename, "wb") as fp:
                    fp.write(image_data)
                _log.info(f"Saved image as {ext}: {alt_filename}")
                saved = True
                break
            except Exception as e:
                _log.debug(f"Could not save as {ext}: {e}")
    
    return saved

def extract_images_from_pdf(input_pdf_path: str, output_dir: str = None):
    """
    Extract images from a PDF using pypdf with improved image handling.
    
    Args:
        input_pdf_path: Path to the input PDF file
        output_dir: Output directory (defaults to PDF name + '_images')
    """
    input_doc_path = Path(input_pdf_path)
    
    if not input_doc_path.exists():
        _log.error(f"PDF file not found: {input_pdf_path}")
        return False
    
    # Create output directory based on PDF name if not specified
    if output_dir is None:
        output_dir = f"{input_doc_path.stem}_images"
    
    output_dir = Path(output_dir)
    
    _log.info(f"Processing PDF: {input_pdf_path}")
    _log.info(f"Output directory: {output_dir}")
    
    start_time = time.time()
    
    try:
        # Open the PDF
        _log.info("Opening PDF and extracting images...")
        reader = PdfReader(input_pdf_path)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        doc_filename = input_doc_path.stem
        
        total_images = 0
        
        # Extract images from each page
        for page_num, page in enumerate(reader.pages):
            _log.info(f"Processing page {page_num + 1}...")
            
            try:
                # Check if page has images
                if hasattr(page, 'images') and page.images:
                    page_images = 0
                    
                    for count, image_file_object in enumerate(page.images):
                        try:
                            # Create filename
                            image_name = image_file_object.name if hasattr(image_file_object, 'name') and image_file_object.name else f"image_{count}"
                            # Remove any file extension from the name to avoid double extensions
                            if '.' in image_name:
                                image_name = image_name.split('.')[0]
                            
                            # Create unique filename with page and image number
                            image_filename = output_dir / f"{doc_filename}_page{page_num + 1}_{image_name}_{count}.png"
                            
                            # Try improved image saving
                            if save_image_with_fallbacks(image_file_object.data, image_filename, image_name):
                                page_images += 1
                                total_images += 1
                            else:
                                _log.warning(f"Failed to save image {count} from page {page_num + 1}")
                            
                        except Exception as e:
                            _log.warning(f"Could not process image {count} from page {page_num + 1}: {e}")
                    
                    if page_images > 0:
                        _log.info(f"Extracted {page_images} images from page {page_num + 1}")
                    else:
                        _log.info(f"No images found on page {page_num + 1}")
                        
                else:
                    _log.info(f"No images found on page {page_num + 1}")
                    
            except Exception as e:
                _log.warning(f"Error processing page {page_num + 1}: {e}")
        
        # Also try to extract images from annotations (like stamps)
        _log.info("Checking for images in annotations...")
        annotation_images = 0
        
        for page_num, page in enumerate(reader.pages):
            try:
                if "/Annots" in page:
                    annotations = page["/Annots"]
                    if annotations:
                        for annot_num, annot_ref in enumerate(annotations):
                            try:
                                annot = annot_ref.get_object()
                                if "/AP" in annot and "/N" in annot["/AP"]:
                                    ap_n = annot["/AP"]["/N"]
                                    if "/Resources" in ap_n and "/XObject" in ap_n["/Resources"]:
                                        xobjects = ap_n["/Resources"]["/XObject"]
                                        for xobj_name, xobj_ref in xobjects.items():
                                            try:
                                                xobj = xobj_ref.get_object()
                                                if "/Subtype" in xobj and xobj["/Subtype"] == "/Image":
                                                    # Try to decode as image
                                                    if hasattr(xobj, 'decode_as_image'):
                                                        image = xobj.decode_as_image()
                                                        annotation_filename = output_dir / f"{doc_filename}_page{page_num + 1}_annotation_{annot_num}_{xobj_name}.png"
                                                        
                                                        # Save with improved handling
                                                        try:
                                                            if image.mode not in ('RGB', 'RGBA'):
                                                                image = image.convert('RGB')
                                                            image.save(annotation_filename, "PNG")
                                                            _log.info(f"Saved annotation image: {annotation_filename}")
                                                            annotation_images += 1
                                                            total_images += 1
                                                        except Exception as e:
                                                            _log.warning(f"Could not save annotation image: {e}")
                                            except Exception as e:
                                                _log.debug(f"Could not extract annotation image: {e}")
                            except Exception as e:
                                _log.debug(f"Could not process annotation: {e}")
            except Exception as e:
                _log.debug(f"Could not check annotations on page {page_num + 1}: {e}")
        
        if annotation_images > 0:
            _log.info(f"Extracted {annotation_images} images from annotations")
        
        end_time = time.time() - start_time
        
        # Summary
        _log.info("=" * 60)
        _log.info("EXTRACTION SUMMARY")
        _log.info("=" * 60)
        _log.info(f"PDF processed: {input_pdf_path}")
        _log.info(f"Processing time: {end_time:.2f} seconds")
        _log.info(f"Total pages: {len(reader.pages)}")
        _log.info(f"Total images extracted: {total_images}")
        _log.info(f"Output directory: {output_dir}")
        if PIL_AVAILABLE:
            _log.info("Note: Look for '.improved.png' files for better quality images")
        else:
            _log.info("Tip: Install Pillow for better image processing: pip install Pillow")
        _log.info("=" * 60)
        
        return True
        
    except Exception as e:
        _log.error(f"Error processing PDF: {e}")
        return False

def list_available_pdfs():
    """List all PDF files in the current directory."""
    current_dir = Path(".")
    pdf_files = list(current_dir.glob("*.pdf"))
    
    if pdf_files:
        _log.info("Available PDF files:")
        for i, pdf_file in enumerate(pdf_files, 1):
            file_size = pdf_file.stat().st_size
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{file_size / 1024:.1f} KB"
            _log.info(f"  {i}. {pdf_file.name} ({size_str})")
    else:
        _log.info("No PDF files found in current directory.")
    
    return pdf_files

def main():
    parser = argparse.ArgumentParser(description="Extract images from PDF using pypdf with improved image handling")
    parser.add_argument("pdf_path", nargs="?", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-l", "--list", action="store_true", help="List available PDFs")
    
    args = parser.parse_args()
    
    if args.list or not args.pdf_path:
        pdf_files = list_available_pdfs()
        
        if not args.pdf_path and pdf_files:
            _log.info("\nTo extract images, run:")
            _log.info("python pypdf_image_extractor.py <pdf_filename>")
            _log.info("\nFor example:")
            _log.info(f"python pypdf_image_extractor.py {pdf_files[0].name}")
        return
    
    # Extract images from the specified PDF
    success = extract_images_from_pdf(args.pdf_path, args.output)
    
    if success:
        _log.info("Image extraction completed successfully!")
    else:
        _log.error("Image extraction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 