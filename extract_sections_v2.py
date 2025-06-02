import json
import os
import argparse
import re
from pdf_cropper import crop_pdf

def sanitize_filename(name):
    """Convert a string to a valid filename by removing invalid characters."""
    # Replace problematic characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def extract_pdf_sections(json_file_path, pdf_file_path, output_dir=None):
    """
    Extract sections from a PDF based on the topic data from topic-data2.json format.
    
    Args:
        json_file_path (str): Path to the JSON file with topic data
        pdf_file_path (str): Path to the source PDF file
        output_dir (str, optional): Directory to save output files, defaults to current directory
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load topic data from JSON
    try:
        with open(json_file_path, 'r') as file:
            topic_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return
    
    # Verify PDF file exists
    if not os.path.exists(pdf_file_path):
        print(f"Error: PDF file not found at {pdf_file_path}")
        return
    
    # Process each topic and its chapters
    for topic_index, topic in enumerate(topic_data.get('topics', []), 1):
        topic_name = topic.get('topic', 'Unknown Topic')
        print(f"\nProcessing topic: {topic_name}")
        
        # Create a folder for this topic with sequence number
        topic_folder_name = f"{topic_index:02d}_{sanitize_filename(topic_name)}"
        topic_folder_path = os.path.join(output_dir, topic_folder_name)
        if not os.path.exists(topic_folder_path):
            os.makedirs(topic_folder_path)
            print(f"  Created folder: {topic_folder_name}")
        
        # In topic-data2.json, sections are called "chapters"
        for chapter in topic.get('chapters', []):
            chapter_title = chapter.get('title', 'Unknown Chapter')
            from_page = chapter.get('from')
            to_page = chapter.get('to')
            
            if from_page is None or to_page is None:
                print(f"  Skipping chapter '{chapter_title}' - missing page numbers")
                continue
            
            # Create filename based on chapter title only (since it's already in the topic folder)
            output_file = os.path.join(topic_folder_path, f"{sanitize_filename(chapter_title)}.pdf")
            
            print(f"  Extracting: {chapter_title} (pages {from_page}-{to_page}) -> {topic_folder_name}/{os.path.basename(output_file)}")
            
            try:
                # Crop the PDF using the function from pdf_cropper.py
                crop_pdf(
                    input_path=pdf_file_path,
                    output_path=output_file,
                    start_page=from_page,
                    end_page=to_page
                )
            except Exception as e:
                print(f"  Error processing chapter '{chapter_title}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PDF sections based on topic data from topic-data2.json")
    parser.add_argument("json_file", help="Path to the JSON file with topic and chapter data")
    parser.add_argument("pdf_file", help="Path to the source PDF file to crop")
    parser.add_argument("-o", "--output_dir", help="Directory to save output files (default: current directory)")
    
    args = parser.parse_args()
    
    extract_pdf_sections(args.json_file, args.pdf_file, args.output_dir) 