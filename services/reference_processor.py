"""
Reference Processor Service
Handles processing of reference documents using docling and creates markdown context files
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional

class ReferenceProcessor:
    def __init__(self, cache_dir: str = "cache/topic-references"):
        self.cache_dir = Path(cache_dir)
        self.references_map_file = self.cache_dir / "references_map.json"
    
    def ensure_directories(self):
        """Ensure all necessary directories exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_references_map(self) -> Dict:
        """Load the topic references mapping"""
        if not self.references_map_file.exists():
            return {}
        try:
            import json
            with open(self.references_map_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    async def create_topic_reference_context(self, cache_key: str, topic_name: str = None) -> Optional[str]:
        """
        Create or update a markdown context file for a topic by processing all reference documents with docling
        Uses cache_key (topic_name) as directory structure
        """
        try:
            from docling.document_converter import DocumentConverter
            
            # Get all references for this topic
            references_map = self.load_references_map()
            
            # References are stored by cache_key in the references_map
            topic_references = references_map.get(cache_key, [])
            
            if not topic_references:
                print(f"No references found for cache key '{cache_key}'")
                return None
            
            # Initialize docling converter
            converter = DocumentConverter()
            
            # Create the context file path using cache_key (topic name)
            topic_dir = self.cache_dir / cache_key
            topic_dir.mkdir(parents=True, exist_ok=True)
            context_file_path = topic_dir / f"{cache_key}_reference_context.md"
            
            # Start building the markdown content
            topic_display_name = cache_key.replace('_', ' ')
            markdown_content = f"# Reference Context for Topic: {topic_display_name}\n\n"
            markdown_content += f"*Auto-generated on {time.strftime('%Y-%m-%d %H:%M:%S')} using Docling*\n\n"
            markdown_content += "---\n\n"
            
            processed_count = 0
            
            for ref in topic_references:
                file_path = ref.get('file_path')
                filename = ref.get('filename', 'Unknown')
                
                if not file_path or not os.path.exists(file_path):
                    print(f"⚠️ Skipping {filename} - file not found")
                    continue
                
                try:
                    print(f"🔄 Processing {filename} with docling...")
                    
                    # Convert document using docling
                    result = converter.convert(file_path)
                    
                    # Extract text content
                    document_text = result.document.export_to_markdown()
                    
                    # Add to markdown content
                    markdown_content += f"## {filename}\n\n"
                    markdown_content += f"**Source:** {filename}\n"
                    markdown_content += f"**Size:** {ref.get('size', 0)} bytes\n"
                    markdown_content += f"**Uploaded:** {ref.get('uploaded_at', 'Unknown')}\n\n"
                    markdown_content += "**Content:**\n\n"
                    markdown_content += document_text
                    markdown_content += "\n\n---\n\n"
                    
                    processed_count += 1
                    print(f"✅ Successfully processed {filename}")
                    
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")
                    # Add error note in the markdown
                    markdown_content += f"## {filename}\n\n"
                    markdown_content += f"**Source:** {filename}\n"
                    markdown_content += f"**Status:** ❌ Error processing document\n"
                    markdown_content += f"**Error:** {str(e)}\n\n"
                    markdown_content += "---\n\n"
                    continue
            
            # Write the context file
            with open(context_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Created reference context file: {context_file_path}")
            print(f"📊 Processed {processed_count}/{len(topic_references)} reference documents")
            
            return str(context_file_path)
            
        except ImportError:
            print("❌ Docling not available for processing reference documents")
            raise Exception("Docling not installed or not available")
        except Exception as e:
            print(f"❌ Error creating reference context: {e}")
            raise e
    
    async def get_topic_reference_context(self, cache_key: str) -> str:
        """
        Get the markdown context content for a topic using cache key (topic name). Returns error if context file doesn't exist.
        """
        try:
            topic_dir = self.cache_dir / cache_key
            context_file_path = topic_dir / f"{cache_key}_reference_context.md"
            
            if not context_file_path.exists():
                raise Exception(f"Reference context file not found for topic '{cache_key}'. Please ensure reference documents are uploaded and processed.")
            
            with open(context_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            raise Exception(f"Error reading reference context for topic '{cache_key}': {str(e)}")
    
    def context_file_exists(self, cache_key: str) -> bool:
        """Check if a reference context file exists for a topic using cache key"""
        topic_dir = self.cache_dir / cache_key
        context_file_path = topic_dir / f"{cache_key}_reference_context.md"
        return context_file_path.exists()
    
    async def process_reference_upload(self, cache_key: str, topic_name: str, uploaded_files: List[Dict]) -> bool:
        """
        Process newly uploaded reference files and update the context file
        """
        try:
            # Create/update the reference context file
            await self.create_topic_reference_context(cache_key, topic_name)
            return True
        except Exception as e:
            print(f"⚠️ Warning: Failed to create reference context file: {e}")
            return False

# Global instance
reference_processor = ReferenceProcessor() 