"""
Case Management Service
Coordinates between assessment case generation and master case document creation
"""

import re
from typing import Dict, List
from .master_case_generator import generate_multiple_master_cases
from .reference_processor import reference_processor

def sanitize_topic_name(topic_name: str) -> str:
    """Sanitize topic name for use as directory name"""
    if not topic_name:
        return topic_name
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w\s-]', '', topic_name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_')

class CaseManagementService:
    
    async def generate_master_cases_from_assessment(
        self, 
        sanitized_topic_name: str, 
        approved_cases: List[Dict], 
        original_topic_data: Dict = None
    ) -> Dict:
        """
        Main coordination function that takes approved assessment cases and generates master case documents
        Note: sanitized_topic_name should already be sanitized (e.g., 'liver_disease')
        """
        try:
            # Validate inputs
            if not sanitized_topic_name or not approved_cases:
                return {
                    "success": False,
                    "message": "Missing required fields: sanitized_topic_name and approved_cases"
                }
            
            # Use the already sanitized topic name as the cache key
            cache_key = sanitized_topic_name
            try:
                references = await reference_processor.get_topic_reference_context(cache_key)
                print(f"✅ Retrieved reference context for sanitized topic '{sanitized_topic_name}' (cache: {cache_key})")
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Reference context not found for sanitized topic '{sanitized_topic_name}': {str(e)}"
                }
            
            # Generate master cases
            print(f"🚀 Starting master case generation for {len(approved_cases)} approved cases")
            result = await generate_multiple_master_cases(approved_cases, references, sanitized_topic_name)
            
            # Format response
            response = {
                "success": True,
                "topic_name": sanitized_topic_name,
                "cache_key": cache_key,
                "generated_cases": result["generated_cases"],
                "failed_cases": result["failed_cases"],
                "total_cases": result["total_cases"],
                "successful_generations": result["successful_generations"],
                "failed_generations": result["failed_generations"],
                "message": f"Generated {result['successful_generations']}/{result['total_cases']} master case documents"
            }
            
            # Log summary
            print(f"📊 Case Generation Summary:")
            print(f"   - Total cases: {result['total_cases']}")
            print(f"   - Successful: {result['successful_generations']}")
            print(f"   - Failed: {result['failed_generations']}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error in case management: {e}")
            return {
                "success": False,
                "message": f"Error generating master cases: {str(e)}"
            }
    
    async def get_topic_status(self, topic_name: str) -> Dict:
        """
        Get the status of a topic including reference availability and any generated cases
        """
        try:
            # Check if reference context exists using cache_key
            cache_key = sanitize_topic_name(topic_name)
            has_references = reference_processor.context_file_exists(cache_key)
            
            # Check for generated cases (scan cache/case_docs for files)
            from pathlib import Path
            case_docs_dir = Path("cache/case_docs")
            generated_cases = []
            
            if case_docs_dir.exists():
                for case_file in case_docs_dir.glob("*.md"):
                    generated_cases.append({
                        "filename": case_file.name,
                        "path": str(case_file),
                        "size": case_file.stat().st_size
                    })
            
            return {
                "topic_name": topic_name,
                "cache_key": cache_key,
                "has_reference_context": has_references,
                "generated_cases_count": len(generated_cases),
                "generated_cases": generated_cases
            }
            
        except Exception as e:
            return {
                "topic_name": topic_name,
                "cache_key": cache_key,
                "error": str(e)
            }

# Global instance
case_manager = CaseManagementService() 