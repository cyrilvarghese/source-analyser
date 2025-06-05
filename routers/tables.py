"""
Tables router for table extraction and processing
"""

import os
import shutil
import time
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/tables", tags=["tables"])

# Table extraction cache utilities
TABLE_CACHE_DIR = Path("cache/table-extractions")
TABLE_CACHE_MAP = TABLE_CACHE_DIR / "cache_map.json"

def ensure_table_cache_dir():
    """Ensure table cache directory exists"""
    TABLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_table_cache_map():
    """Load the table cache mapping"""
    if not TABLE_CACHE_MAP.exists():
        return {}
    try:
        with open(TABLE_CACHE_MAP, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_table_cache_map(cache_map):
    """Save the table cache mapping"""
    ensure_table_cache_dir()
    try:
        with open(TABLE_CACHE_MAP, 'w') as f:
            json.dump(cache_map, f, indent=2)
    except IOError as e:
        print(f"Error saving table cache map: {e}")

def has_table_cache(filename):
    """Check if a file has cached table extraction results"""
    cache_map = load_table_cache_map()
    if filename not in cache_map:
        return False
    
    cache_entry = cache_map[filename]
    json_exists = os.path.exists(cache_entry.get('json_file', ''))
    markdown_exists = os.path.exists(cache_entry.get('markdown_file', ''))
    
    return json_exists and markdown_exists

def get_table_cache(filename):
    """Get cached table extraction results"""
    if not has_table_cache(filename):
        return None
    
    cache_map = load_table_cache_map()
    cache_entry = cache_map[filename]
    
    try:
        # Load JSON data
        with open(cache_entry['json_file'], 'r') as f:
            json_data = json.load(f)
        
        # Load markdown content
        with open(cache_entry['markdown_file'], 'r') as f:
            markdown_content = f.read()
        
        return {
            'json_data': json_data,
            'markdown_content': markdown_content,
            'cached_at': cache_entry.get('cached_at', 'unknown')
        }
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading cached data: {e}")
        return None

def save_table_cache(filename, json_data, markdown_content):
    """Save table extraction results to cache"""
    ensure_table_cache_dir()
    
    # Generate file paths
    base_name = Path(filename).stem
    timestamp = int(time.time())
    json_filename = f"{base_name}_{timestamp}.json"
    markdown_filename = f"{base_name}_{timestamp}.md"
    
    json_path = TABLE_CACHE_DIR / json_filename
    markdown_path = TABLE_CACHE_DIR / markdown_filename
    
    try:
        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Save markdown file
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        
        # Update cache map
        cache_map = load_table_cache_map()
        cache_map[filename] = {
            'json_file': str(json_path),
            'markdown_file': str(markdown_path),
            'cached_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        save_table_cache_map(cache_map)
        
        return {
            'json_file': str(json_path),
            'markdown_file': str(markdown_path)
        }
    except IOError as e:
        print(f"Error saving to cache: {e}")
        return None

@router.post("/extract-json/")
async def extract_table_json(
    file: UploadFile = File(...)
):
    """
    Extract tables from uploaded file and convert to JSON using Gemini API.
    Returns clean JSON data structure with caching support.
    """
    try:
        # Check cache first
        cached_data = get_table_cache(file.filename)
        if cached_data:
            print(f"✅ Found cached data for {file.filename}")
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "cached": True,
                "cached_at": cached_data['cached_at'],
                "json_data": cached_data['json_data'],
                "processing_time": "0.00s (cached)"
            })
        
        print(f"🔄 Processing {file.filename} - no cache found")
        
        import pandas as pd
        from docling.document_converter import DocumentConverter
        from google import genai
        
        start_time = time.time()
        
        # Create directories for processing
        temp_output_dir = Path("temp_processing")
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        temp_file_path = temp_output_dir / f"temp_{int(time.time())}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing file with Docling: {file.filename}")
        
        # Initialize Docling document converter
        doc_converter = DocumentConverter()
        
        # Convert the document
        conv_res = doc_converter.convert(temp_file_path)
        
        # Extract tables to markdown
        tables_markdown = []
        for table_ix, table in enumerate(conv_res.document.tables):
            table_df: pd.DataFrame = table.export_to_dataframe()
            table_markdown = table_df.to_markdown(index=False)
            tables_markdown.append({
                "table_number": table_ix + 1,
                "markdown": table_markdown,
                "rows": len(table_df),
                "columns": len(table_df.columns) if not table_df.empty else 0
            })
        
        if not tables_markdown:
            # Clean up
            temp_file_path.unlink()
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No tables found in the uploaded file"
                }
            )
        
        # Get API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "GEMINI_API_KEY not found in environment variables. Please add it to your .env file."
                }
            )
        
        # Initialize Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        # Prepare prompt for Gemini
        combined_markdown = "\n\n".join([t["markdown"] for t in tables_markdown])
        
        prompt = f"""You are a medical education data extractor. Convert the following markdown table(s) to the EXACT JSON format specified below.

REQUIRED OUTPUT FORMAT (follow this structure exactly):
{{
  "department": "Department Name",
  "topics": [
    {{
      "topic": "Topic Name", 
      "competencies": [
        {{
          "number": "DR1.1",
          "competency": "Full competency description text",
          "teaching_methods": ["LGT", "SGT", "Bedside teaching"],
          "assessment_methods": ["Written", "OSCE", "Tutorials"]
        }}
      ]
    }}
  ]
}}

EXTRACTION RULES:
1. DEPARTMENT: Extract from table title, filename, or context. Use "Medical Education" if unclear.

2. TOPICS: Group competencies logically by:
   - Table sections/headers
   - Subject areas (e.g., "Acne", "Dermatology", "Cardiology")
   - Similar content themes
   - If no clear grouping, use "General"

3. COMPETENCY NUMBER: Look for codes like:
   - DR1.1, DR2.3, GM6.22, IM4.5, etc.
   - Any alphanumeric identifier in first column
   - If missing, generate as "COMP1", "COMP2", etc.

4. COMPETENCY TEXT: Extract full descriptive text (usually longest text field)

5. TEACHING METHODS: Convert text to array. Look for these terms:
   - LGT (Large Group Teaching)
   - SGT (Small Group Teaching) 
   - Bedside teaching
   - Demonstration
   - DOAP (Demonstration, Observation, Assistance, Performance)
   - SDL (Self Directed Learning)
   - Seminar
   - Tutorial
   - Role Play
   - Simulation
   - Flipped Classroom
   - Clinic
   - Video LGT
   - Symposium
   Split by: commas, semicolons, line breaks, "and", "&"

6. ASSESSMENT METHODS: Convert text to array. Look for these terms:
   - Written
   - OSCE (Objective Structured Clinical Examination)
   - Tutorials
   - Direct Observation
   - Case Based Discussion
   - Viva Voce
   - DOPS (Direct Observation of Procedural Skills)
   - Mini CEX
   - Picture based MCQs
   - Prescription writing
   - Rating scale
   - Portfolio
   - Log book
   Split by: commas, semicolons, line breaks, "and", "&"

IMPORTANT INSTRUCTIONS:
- Always return valid JSON only, no explanations
- Use exactly the field names shown: "department", "topics", "topic", "competencies", "number", "competency", "teaching_methods", "assessment_methods"
- Arrays must be arrays even if single item: ["LGT"] not "LGT"
- Handle empty/missing data gracefully with empty arrays [] or "Unknown"
- Clean up text: remove extra spaces, line breaks, special characters
- Ensure all competencies have all required fields

INPUT DATA:
{combined_markdown}

OUTPUT (JSON only):"""

        print("Sending to Gemini API for JSON conversion...")
        
        # Send to Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
        
        # Parse the response
        json_response = response.text.strip()
        
        # Try to clean up any potential markdown formatting
        if json_response.startswith("```json"):
            json_response = json_response.replace("```json", "").replace("```", "").strip()
        elif json_response.startswith("```"):
            json_response = json_response.replace("```", "").strip()
        
        # Validate it's valid JSON
        import json
        try:
            parsed_json = json.loads(json_response)
            
            # Validate the structure and fix any issues
            if not isinstance(parsed_json, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure required fields exist
            if "department" not in parsed_json:
                parsed_json["department"] = "Medical Education"
            
            if "topics" not in parsed_json or not isinstance(parsed_json["topics"], list):
                parsed_json["topics"] = []
            
            # Validate and fix each topic
            for topic in parsed_json["topics"]:
                if "topic" not in topic:
                    topic["topic"] = "General"
                
                if "competencies" not in topic or not isinstance(topic["competencies"], list):
                    topic["competencies"] = []
                
                # Validate and fix each competency
                for comp in topic["competencies"]:
                    if "number" not in comp:
                        comp["number"] = "COMP1"
                    if "competency" not in comp:
                        comp["competency"] = "Unknown competency"
                    if "teaching_methods" not in comp or not isinstance(comp["teaching_methods"], list):
                        comp["teaching_methods"] = []
                    if "assessment_methods" not in comp or not isinstance(comp["assessment_methods"], list):
                        comp["assessment_methods"] = []
            
            print(f"✅ Successfully parsed and validated JSON with {len(parsed_json['topics'])} topics")
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ JSON parsing/validation error: {e}")
            print(f"Response was: {json_response[:500]}...")
            
            # Fallback: create structured data from the original table
            print("🔄 Using fallback data structure creation...")
            topics = []
            
            for t_idx, (table_info, table) in enumerate(zip(tables_markdown, conv_res.document.tables)):
                table_df = table.export_to_dataframe()
                if not table_df.empty:
                    competencies = []
                    
                    # Get column names
                    if table_df.columns.tolist() == list(range(len(table_df.columns))):
                        column_names = [f"column{i+1}" for i in range(len(table_df.columns))]
                    else:
                        column_names = list(table_df.columns)
                    
                    print(f"Processing table {t_idx+1} with columns: {column_names}")
                    
                    # Convert each row to a competency
                    for row_idx, row in table_df.iterrows():
                        # Try to extract meaningful data
                        comp_data = {
                            "number": f"COMP{row_idx+1}",
                            "competency": "Unknown competency",
                            "teaching_methods": [],
                            "assessment_methods": []
                        }
                        
                        # Look for code/number in first column
                        if len(column_names) > 0 and not pd.isna(row.iloc[0]):
                            first_val = str(row.iloc[0]).strip()
                            if first_val and len(first_val) < 20:  # Likely a code
                                comp_data["number"] = first_val
                        
                        # Look for competency description in longest text field
                        longest_text = ""
                        for col_idx, val in enumerate(row):
                            if not pd.isna(val):
                                text_val = str(val).strip()
                                if len(text_val) > len(longest_text):
                                    longest_text = text_val
                        
                        if longest_text:
                            comp_data["competency"] = longest_text
                        
                        # Try to extract teaching and assessment methods from other columns
                        for col_idx, val in enumerate(row):
                            if not pd.isna(val):
                                text_val = str(val).strip().lower()
                                
                                # Check for teaching methods
                                teaching_keywords = ['lgt', 'sgt', 'bedside', 'demonstration', 'doap', 'sdl', 'seminar', 'tutorial', 'role play', 'simulation']
                                for keyword in teaching_keywords:
                                    if keyword in text_val:
                                        method = keyword.upper() if keyword in ['lgt', 'sgt', 'sdl', 'doap'] else keyword.title()
                                        if method not in comp_data["teaching_methods"]:
                                            comp_data["teaching_methods"].append(method)
                                
                                # Check for assessment methods
                                assessment_keywords = ['written', 'osce', 'tutorials', 'observation', 'viva', 'dops', 'mcq']
                                for keyword in assessment_keywords:
                                    if keyword in text_val:
                                        method = keyword.upper() if keyword in ['osce', 'dops'] else keyword.title()
                                        if method not in comp_data["assessment_methods"]:
                                            comp_data["assessment_methods"].append(method)
                        
                        # Only add if we have meaningful data
                        if comp_data["competency"] != "Unknown competency" or comp_data["teaching_methods"] or comp_data["assessment_methods"]:
                            competencies.append(comp_data)
                    
                    # Create topic
                    if competencies:
                        topic_name = f"Table {t_idx+1}"
                        # Try to extract topic from table context
                        if table_info.get("markdown"):
                            first_line = table_info["markdown"].split('\n')[0].strip()
                            if len(first_line) < 50 and first_line:
                                topic_name = first_line
                        
                        topics.append({
                            "topic": topic_name,
                            "competencies": competencies
                        })
            
            parsed_json = {
                "department": "Medical Education",
                "topics": topics
            }
            print(f"🔧 Created fallback structure with {len(topics)} topics")
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        processing_time = time.time() - start_time
        
        print(f"Processing completed in {processing_time:.2f}s")
        print(f"Found {len(tables_markdown)} table(s)")
        
        # Save to cache
        markdown_content = "\n\n".join([t["markdown"] for t in tables_markdown])
        cache_result = save_table_cache(file.filename, parsed_json, markdown_content)
        if cache_result:
            print(f"💾 Saved to cache: {cache_result}")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "tables_found": len(tables_markdown),
            "processing_time": f"{processing_time:.2f}s",
            "json_data": parsed_json,
            "cached": False
        })
        
    except ImportError as e:
        print(f"Import error: {e}")
        if "google" in str(e):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Google GenAI SDK not installed. Please install with: pip install google-genai"
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Required dependencies not installed. Please install with: pip install docling docling-core pandas google-genai"
                }
            )
    except Exception as e:
        print(f"Error processing table: {e}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing table: {str(e)}"
            }
        )

@router.get("/cache/list/")
async def list_cached_tables():
    """List all cached table extraction results."""
    try:
        cache_map = load_table_cache_map()
        return JSONResponse(content={
            "success": True,
            "cached_files": len(cache_map),
            "cache": cache_map
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error listing cache: {str(e)}"
            }
        )

@router.delete("/cache/{filename}")
async def clear_table_cache(filename: str):
    """Clear cache for a specific file."""
    try:
        cache_map = load_table_cache_map()
        if filename in cache_map:
            cache_entry = cache_map[filename]
            # Remove files
            for file_path in [cache_entry.get('json_file'), cache_entry.get('markdown_file')]:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            # Remove from map
            del cache_map[filename]
            save_table_cache_map(cache_map)
            return JSONResponse(content={
                "success": True,
                "message": f"Cache cleared for {filename}"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"No cache found for {filename}"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error clearing cache: {str(e)}"
            }
        ) 

@router.post("/process/")
async def process_table(
    file: UploadFile = File(...),
    generate_csv: bool = Form(True),
    generate_html: bool = Form(True),
    generate_markdown: bool = Form(True)
):
    """
    Process a table image using Docling to extract tables and generate various formats with caching support.
    Based on the docling table export example.
    """
    try:
        # Check cache first for basic table extraction
        cached_data = get_table_cache(file.filename)
        if cached_data:
            print(f"✅ Found cached table data for {file.filename}")
            # Note: For the /process/ endpoint, we still need to generate the files,
            # but we can skip the expensive table extraction part
            
        import pandas as pd
        from docling.document_converter import DocumentConverter
        
        start_time = time.time()
        
        # Create directories for table processing
        table_output_dir = Path("extracted-data") / "table-extractions"
        table_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        temp_file_path = table_output_dir / f"temp_{int(time.time())}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Processing table image: {file.filename}")
        print(f"Temporary file saved to: {temp_file_path}")
        
        # Initialize Docling document converter
        doc_converter = DocumentConverter()
        
        # Convert the document
        conv_res = doc_converter.convert(temp_file_path)
        
        # Create unique output directory for this processing
        doc_filename = temp_file_path.stem
        output_dir = table_output_dir / f"{doc_filename}_{int(time())}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "success": True,
            "filename": file.filename,
            "tables_found": len(conv_res.document.tables),
            "processing_time": f"{time.time() - start_time:.2f}s",
            "output_dir": str(output_dir),
            "files": [],
            "tables": [],
            "markdown_content": ""
        }
        
        # Process each table found in the document
        all_markdown_tables = []
        
        for table_ix, table in enumerate(conv_res.document.tables):
            table_num = table_ix + 1
            print(f"Processing table {table_num}")
            
            # Export table to dataframe
            table_df: pd.DataFrame = table.export_to_dataframe()
            
            # Generate markdown for this table
            table_markdown = table_df.to_markdown(index=False)
            all_markdown_tables.append(f"## Table {table_num}\n\n{table_markdown}\n")
            
            table_info = {
                "table_number": table_num,
                "rows": len(table_df),
                "columns": len(table_df.columns) if not table_df.empty else 0,
                "markdown": table_markdown
            }
            
            # Generate CSV if requested
            if generate_csv:
                csv_filename = f"{doc_filename}-table-{table_num}.csv"
                csv_path = output_dir / csv_filename
                table_df.to_csv(csv_path, index=False)
                
                # Add to results
                results["files"].append({
                    "filename": csv_filename,
                    "type": "csv",
                    "url": f"/extracted-data/table-extractions/{output_dir.name}/{csv_filename}",
                    "size": csv_path.stat().st_size
                })
                table_info["csv"] = table_df.to_csv(index=False)
            
            # Generate HTML if requested
            if generate_html:
                html_filename = f"{doc_filename}-table-{table_num}.html"
                html_path = output_dir / html_filename
                
                # Generate HTML table
                html_content = table.export_to_html(doc=conv_res.document)
                
                # Create a complete HTML document
                full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Table {table_num} - {file.filename}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-800 mb-4">Table {table_num}</h1>
        <p class="text-gray-600 mb-6">Extracted from: {file.filename}</p>
        <div class="bg-white rounded-lg shadow-md p-6 overflow-x-auto">
            {html_content}
        </div>
    </div>
</body>
</html>"""
                
                with html_path.open("w", encoding="utf-8") as fp:
                    fp.write(full_html)
                
                results["files"].append({
                    "filename": html_filename,
                    "type": "html",
                    "url": f"/extracted-data/table-extractions/{output_dir.name}/{html_filename}",
                    "size": html_path.stat().st_size
                })
                table_info["html"] = html_content
            
            results["tables"].append(table_info)
        
        # Generate combined markdown file if requested
        if generate_markdown and all_markdown_tables:
            markdown_filename = f"{doc_filename}-tables.md"
            markdown_path = output_dir / markdown_filename
            
            combined_markdown = f"""# Tables Extracted from {file.filename}

*Generated using Docling on {time.strftime('%Y-%m-%d %H:%M:%S')}*

---

{chr(10).join(all_markdown_tables)}

---

**Processing Summary:**
- Tables found: {len(conv_res.document.tables)}
- Processing time: {results["processing_time"]}
- Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with markdown_path.open("w", encoding="utf-8") as fp:
                fp.write(combined_markdown)
            
            results["files"].append({
                "filename": markdown_filename,
                "type": "markdown",
                "url": f"/extracted-data/table-extractions/{output_dir.name}/{markdown_filename}",
                "size": markdown_path.stat().st_size
            })
            
            results["markdown_content"] = combined_markdown
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        print(f"Table processing completed in {results['processing_time']}")
        print(f"Found {results['tables_found']} tables")
        print(f"Generated {len(results['files'])} files")
        
        return JSONResponse(content=results)
        
    except ImportError as e:
        print(f"Import error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Docling or required dependencies not installed. Please install with: pip install docling docling-core pandas"
            }
        )
    except Exception as e:
        print(f"Error processing table: {e}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing table: {str(e)}"
            }
        ) 