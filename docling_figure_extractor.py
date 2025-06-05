import logging
import time
from pathlib import Path
import argparse
import sys

try:
    from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
except ImportError:
    print("Error: Docling is not installed.")
    print("Please install docling with: pip install docling docling-core")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_log = logging.getLogger(__name__)

# Image resolution scale (2.0 = high quality, 1.0 = standard 72 DPI)
IMAGE_RESOLUTION_SCALE = 2.0

def extract_figures_with_docling(input_pdf_path: str, output_dir: str = None):
    """
    Extract figures, tables, and page images from a PDF using Docling.
    Based on the approach from: https://dev.to/aairom/figure-export-from-docling-exporting-pdf-to-image-4lp6
    
    Args:
        input_pdf_path: Path to the input PDF file
        output_dir: Output directory (defaults to PDF name + '_docling_extracted' in extracted-data folder)
    """
    input_doc_path = Path(input_pdf_path)
    
    if not input_doc_path.exists():
        _log.error(f"PDF file not found: {input_pdf_path}")
        return False
    
    # Create base extracted-data directory
    base_extracted_dir = Path("extracted-data")
    base_extracted_dir.mkdir(exist_ok=True)
    
    # Create output directory based on PDF name if not specified
    if output_dir is None:
        output_dir = f"{input_doc_path.stem}_docling_extracted"
    
    # Ensure output directory is within extracted-data
    if not str(output_dir).startswith("extracted-data"):
        output_dir = base_extracted_dir / output_dir
    else:
        output_dir = Path(output_dir)
    
    _log.info(f"Processing PDF with Docling: {input_pdf_path}")
    _log.info(f"Output directory: {output_dir}")
    
    start_time = time.time()
    
    try:
        # Important: For operating with page images, we must keep them, otherwise the DocumentConverter
        # will destroy them for cleaning up memory.
        # This is done by setting PdfPipelineOptions.images_scale, which also defines the scale of images.
        # scale=1 correspond of a standard 72 DPI image
        # The PdfPipelineOptions.generate_* are the selectors for the document elements which will be enriched
        # with the image field
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True

        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        _log.info("Converting PDF and extracting content with Docling...")
        conv_res = doc_converter.convert(input_doc_path)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        doc_filename = conv_res.input.file.stem

        # Save page images
        _log.info("Extracting page images...")
        page_count = 0
        for page_no, page in conv_res.document.pages.items():
            page_no = page.page_no
            page_image_filename = output_dir / f"{doc_filename}-page-{page_no}.png"
            
            try:
                if hasattr(page, 'image') and page.image is not None:
                    with page_image_filename.open("wb") as fp:
                        page.image.pil_image.save(fp, format="PNG")
                    page_count += 1
                    _log.info(f"Saved page {page_no} image: {page_image_filename}")
                else:
                    _log.info(f"No image available for page {page_no}")
            except Exception as e:
                _log.warning(f"Could not save page {page_no} image: {e}")

        # Save images of figures and tables
        _log.info("Extracting figures and tables...")
        table_counter = 0
        picture_counter = 0
        
        for element, _level in conv_res.document.iterate_items():
            if isinstance(element, TableItem):
                table_counter += 1
                element_image_filename = (
                    output_dir / f"{doc_filename}-table-{table_counter}.png"
                )
                try:
                    with element_image_filename.open("wb") as fp:
                        element.get_image(conv_res.document).save(fp, "PNG")
                    _log.info(f"Saved table {table_counter}: {element_image_filename}")
                except Exception as e:
                    _log.warning(f"Could not save table {table_counter}: {e}")

            if isinstance(element, PictureItem):
                picture_counter += 1
                element_image_filename = (
                    output_dir / f"{doc_filename}-picture-{picture_counter}.png"
                )
                try:
                    with element_image_filename.open("wb") as fp:
                        element.get_image(conv_res.document).save(fp, "PNG")
                    _log.info(f"Saved picture {picture_counter}: {element_image_filename}")
                except Exception as e:
                    _log.warning(f"Could not save picture {picture_counter}: {e}")

        # Save markdown with embedded pictures
        _log.info("Generating markdown with embedded images...")
        md_filename = output_dir / f"{doc_filename}-with-images.md"
        try:
            conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.EMBEDDED)
            _log.info(f"Saved markdown with embedded images: {md_filename}")
        except Exception as e:
            _log.warning(f"Could not save markdown with embedded images: {e}")

        # Save markdown with externally referenced pictures
        _log.info("Generating markdown with image references...")
        md_filename_refs = output_dir / f"{doc_filename}-with-image-refs.md"
        try:
            conv_res.document.save_as_markdown(md_filename_refs, image_mode=ImageRefMode.REFERENCED)
            _log.info(f"Saved markdown with image references: {md_filename_refs}")
        except Exception as e:
            _log.warning(f"Could not save markdown with image references: {e}")

        # Save HTML with externally referenced pictures
        _log.info("Generating HTML output...")
        html_filename = output_dir / f"{doc_filename}-with-image-refs.html"
        try:
            conv_res.document.save_as_html(html_filename, image_mode=ImageRefMode.REFERENCED)
            _log.info(f"Saved HTML with image references: {html_filename}")
        except Exception as e:
            _log.warning(f"Could not save HTML: {e}")

        end_time = time.time() - start_time

        # Summary
        _log.info("=" * 60)
        _log.info("DOCLING EXTRACTION SUMMARY")
        _log.info("=" * 60)
        _log.info(f"PDF processed: {input_pdf_path}")
        _log.info(f"Processing time: {end_time:.2f} seconds")
        _log.info(f"Page images extracted: {page_count}")
        _log.info(f"Tables extracted: {table_counter}")
        _log.info(f"Pictures/Figures extracted: {picture_counter}")
        _log.info(f"Output directory: {output_dir}")
        _log.info(f"Markdown (embedded): {md_filename}")
        _log.info(f"Markdown (referenced): {md_filename_refs}")
        _log.info(f"HTML output: {html_filename}")
        _log.info("=" * 60)
        _log.info(f"Document converted and figures exported successfully!")

        return True

    except Exception as e:
        _log.error(f"Error processing PDF with Docling: {e}")
        _log.error(f"Make sure you have installed: pip install docling docling-core")
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
    parser = argparse.ArgumentParser(description="Extract figures from PDF using Docling (based on dev.to article)")
    parser.add_argument("pdf_path", nargs="?", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-l", "--list", action="store_true", help="List available PDFs")
    
    args = parser.parse_args()
    
    if args.list or not args.pdf_path:
        pdf_files = list_available_pdfs()
        
        if not args.pdf_path and pdf_files:
            _log.info("\nTo extract figures with Docling, run:")
            _log.info("python docling_figure_extractor.py <pdf_filename>")
            _log.info("\nFor example:")
            _log.info(f"python docling_figure_extractor.py {pdf_files[0].name}")
            _log.info("\nNote: This uses Docling for advanced PDF understanding and figure extraction")
        return
    
    # Extract figures from the specified PDF
    success = extract_figures_with_docling(args.pdf_path, args.output)
    
    if success:
        _log.info("✅ Docling figure extraction completed successfully!")
    else:
        _log.error("❌ Docling figure extraction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 