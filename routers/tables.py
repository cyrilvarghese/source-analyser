"""
Tables router for table extraction and processing
"""

import os
import shutil
import time
import json
import re
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter(prefix="/api/tables", tags=["tables"])

# Table extraction cache utilities
TABLE_CACHE_DIR = Path("cache/table-extractions")
TABLE_CACHE_MAP = TABLE_CACHE_DIR / "cache_map.json"

# Assessment cache utilities
ASSESSMENT_CACHE_DIR = Path("cache/assessments")
ASSESSMENT_CACHE_MAP = ASSESSMENT_CACHE_DIR / "assessment_cache_map.json"

# Topic references directory
TOPIC_REFERENCES_DIR = Path("cache/topic-references")
TOPIC_REFERENCES_MAP = TOPIC_REFERENCES_DIR / "references_map.json"

def sanitize_topic_name(topic_name: str) -> str:
    """Sanitize topic name for use as directory name"""
    if not topic_name:
        return topic_name
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w\s-]', '', topic_name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_')

def ensure_topic_references_dir():
    """Ensure topic references directory exists"""
    TOPIC_REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

def load_topic_references_map():
    """Load the topic references mapping"""
    if not TOPIC_REFERENCES_MAP.exists():
        return {}
    try:
        with open(TOPIC_REFERENCES_MAP, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_topic_references_map(references_map):
    """Save the topic references mapping"""
    ensure_topic_references_dir()
    try:
        with open(TOPIC_REFERENCES_MAP, 'w') as f:
            json.dump(references_map, f, indent=2)
    except IOError as e:
        print(f"Error saving topic references map: {e}")

def ensure_assessment_cache_dir():
    """Ensure assessment cache directory exists"""
    ASSESSMENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_assessment_cache_map():
    """Load the assessment cache mapping"""
    if not ASSESSMENT_CACHE_MAP.exists():
        return {}
    try:
        with open(ASSESSMENT_CACHE_MAP, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_assessment_cache_map(cache_map):
    """Save the assessment cache mapping"""
    ensure_assessment_cache_dir()
    try:
        with open(ASSESSMENT_CACHE_MAP, 'w') as f:
            json.dump(cache_map, f, indent=2)
    except IOError as e:
        print(f"Error saving assessment cache map: {e}")

def save_assessment_cache(cache_data):
    """Save assessment result to cache"""
    ensure_assessment_cache_dir()
    
    # Generate file path using sanitized topic name as cache key
    topic_name = cache_data.get('topic', 'Unknown_Topic')
    sanitized_topic = sanitize_topic_name(topic_name)
    cache_id = sanitized_topic if sanitized_topic else f"topic_{int(time.time())}"
    
    json_filename = f"{cache_id}.json"
    json_path = ASSESSMENT_CACHE_DIR / json_filename
    
    try:
        # Check if cache already exists and remove old file
        cache_map = load_assessment_cache_map()
        if cache_id in cache_map:
            old_json_file = cache_map[cache_id].get('json_file')
            if old_json_file and os.path.exists(old_json_file):
                try:
                    os.remove(old_json_file)
                    print(f"Replaced existing cache for topic: {topic_name}")
                except OSError:
                    pass  # File might be in use or already deleted
        
        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        # Update cache map
        cache_map[cache_id] = {
            'type': 'assessment',
            'json_file': str(json_path),
            'topic': cache_data.get('topic', 'Unknown Topic'),
            'created_at': cache_data.get('createdAt', ''),
            'cases_count': cache_data.get('casesCount', 0),
            'competencies_count': cache_data.get('competenciesCount', 0),
            'coverage_percentage': cache_data.get('coveragePercentage', 0),
            'cache_id': cache_id  # Store the topic-based cache ID
        }
        save_assessment_cache_map(cache_map)
        
        return str(json_path)
    except IOError as e:
        print(f"Error saving assessment to cache: {e}")
        return None

def get_assessment_cache(cache_id):
    """Get cached assessment result"""
    cache_map = load_assessment_cache_map()
    if cache_id not in cache_map:
        return None
    
    cache_entry = cache_map[cache_id]
    json_file = cache_entry.get('json_file')
    
    if not json_file or not os.path.exists(json_file):
        return None
    
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading cached assessment: {e}")
        return None

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
            'type': 'table',
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

@router.get("/cached-files/")
async def list_cached_files():
    """List all cached table extraction files in the format expected by the frontend."""
    try:
        cache_map = load_table_cache_map()
        cached_files = []
        
        for filename, cache_entry in cache_map.items():
            try:
                # Load JSON data to get metadata
                json_file = cache_entry.get('json_file')
                if json_file and os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                    
                    # Extract metadata
                    department = json_data.get('department', 'Unknown Department')
                    topics = json_data.get('topics', [])
                    topics_count = len(topics)
                    competencies_count = sum(len(topic.get('competencies', [])) for topic in topics)
                    
                    # Generate file ID from the JSON filename
                    file_id = Path(json_file).stem
                    
                    cached_files.append({
                        "id": file_id,
                        "filename": filename,
                        "processedDate": cache_entry.get('cached_at', 'unknown'),
                        "department": department,
                        "topicsCount": topics_count,
                        "competenciesCount": competencies_count
                    })
            except Exception as e:
                print(f"Error processing cache entry for {filename}: {e}")
                continue
        
        return JSONResponse(content=cached_files)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error listing cached files: {str(e)}"
            }
        )

@router.get("/cached-files/{file_id}/")
async def get_cached_file(file_id: str):
    """Get a specific cached file's data by file ID."""
    try:
        cache_map = load_table_cache_map()
        
        # Find the cache entry that matches the file_id
        matching_entry = None
        matching_filename = None
        
        for filename, cache_entry in cache_map.items():
            json_file = cache_entry.get('json_file')
            if json_file and Path(json_file).stem == file_id:
                matching_entry = cache_entry
                matching_filename = filename
                break
        
        if not matching_entry:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Cached file with ID {file_id} not found"
                }
            )
        
        # Load the cached data
        cached_data = get_table_cache(matching_filename)
        if not cached_data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Cache data not found or corrupted for {file_id}"
                }
            )
        
        # Extract metadata from the JSON data
        json_data = cached_data['json_data']
        department = json_data.get('department', 'Unknown Department')
        topics = json_data.get('topics', [])
        topics_count = len(topics)
        competencies_count = sum(len(topic.get('competencies', [])) for topic in topics)
        
        return JSONResponse(content={
            "id": file_id,
            "filename": matching_filename,
            "processedDate": cached_data['cached_at'],
            "department": department,
            "topicsCount": topics_count,
            "competenciesCount": competencies_count,
            "data": json_data
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error loading cached file: {str(e)}"
            }
        )

@router.post("/topics/{topic_name}/references/")
async def attach_reference_to_topic(
    topic_name: str,
    files: list[UploadFile] = File(...),
    description: str = Form("")
):
    """Attach one or more reference documents to a specific topic."""
    try:
        ensure_topic_references_dir()
        
        # Use sanitized topic_name as cache key
        if not topic_name:
            raise HTTPException(status_code=400, detail="topic_name is required")
            
        cache_key = sanitize_topic_name(topic_name)
        topic_dir = TOPIC_REFERENCES_DIR / cache_key
        topic_dir.mkdir(parents=True, exist_ok=True)
        
        # Update references map (use cache_key as the key for consistency)
        references_map = load_topic_references_map()
        if cache_key not in references_map:
            references_map[cache_key] = []
        
        uploaded_references = []
        
        # Process each file
        for file in files:
            # Generate unique filename with timestamp
            timestamp = int(time.time())
            file_extension = Path(file.filename).suffix
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = topic_dir / safe_filename
            
            # Save the uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            reference_entry = {
                "id": f"{topic_name}_{timestamp}_{len(uploaded_references)}",
                "filename": file.filename,
                "safe_filename": safe_filename,
                "description": description,
                "file_path": str(file_path),
                "size": file_path.stat().st_size,
                "uploaded_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "mime_type": file.content_type,
                "topic_name": topic_name,
                "cache_key": cache_key
            }
            
            references_map[cache_key].append(reference_entry)
            uploaded_references.append(reference_entry)
            
            # Small delay to ensure unique timestamps
            time.sleep(0.01)
        
        save_topic_references_map(references_map)
        
        # Generate/update the markdown context file for this topic
        try:
            from services.reference_processor import reference_processor
            await reference_processor.create_topic_reference_context(cache_key, topic_name)
            print(f"✅ Updated reference context file for topic '{topic_name}' (cache: {cache_key})")
        except Exception as e:
            print(f"⚠️ Warning: Failed to create reference context file: {e}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"{len(uploaded_references)} reference document(s) attached to topic '{topic_name}'",
            "topic_name": topic_name,
            "cache_key": cache_key,
            "references": uploaded_references,
            "count": len(uploaded_references)
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error attaching reference(s): {str(e)}"
            }
        )

@router.get("/topics/{topic_name}/references/")
async def list_topic_references(topic_name: str):
    """List all reference documents for a specific topic."""
    try:
        cache_key = sanitize_topic_name(topic_name)
        references_map = load_topic_references_map()
        topic_references = references_map.get(cache_key, [])
        
        # Filter out references where files no longer exist
        valid_references = []
        for ref in topic_references:
            if os.path.exists(ref.get('file_path', '')):
                valid_references.append(ref)
        
        # Update map if we removed any invalid references
        if len(valid_references) != len(topic_references):
            references_map[cache_key] = valid_references
            save_topic_references_map(references_map)
        
        return JSONResponse(content={
            "success": True,
            "topic_name": topic_name,
            "references": valid_references
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error listing references: {str(e)}"
            }
        )

@router.get("/topics/{topic_name}/references/{reference_id}/download/")
async def download_topic_reference(topic_name: str, reference_id: str):
    """Download a specific reference document."""
    try:
        cache_key = sanitize_topic_name(topic_name)
        references_map = load_topic_references_map()
        topic_references = references_map.get(cache_key, [])
        
        # Find the reference
        reference = None
        for ref in topic_references:
            if ref.get('id') == reference_id:
                reference = ref
                break
        
        if not reference:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Reference {reference_id} not found for topic {topic_name}"
                }
            )
        
        file_path = reference.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Reference file not found"
                }
            )
        
        return FileResponse(
            path=file_path,
            filename=reference.get('filename', 'download'),
            media_type=reference.get('mime_type', 'application/octet-stream')
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error downloading reference: {str(e)}"
            }
        )

@router.delete("/topics/{topic_name}/references/{reference_id}/")
async def delete_topic_reference(topic_name: str, reference_id: str):
    """Delete a reference document from a topic."""
    try:
        cache_key = sanitize_topic_name(topic_name)
        references_map = load_topic_references_map()
        topic_references = references_map.get(cache_key, [])
        
        # Find and remove the reference
        reference_to_delete = None
        updated_references = []
        
        for ref in topic_references:
            if ref.get('id') == reference_id:
                reference_to_delete = ref
            else:
                updated_references.append(ref)
        
        if not reference_to_delete:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Reference {reference_id} not found for topic {topic_name}"
                }
            )
        
        # Delete the file
        file_path = reference_to_delete.get('file_path')
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Update references map
        references_map[cache_key] = updated_references
        save_topic_references_map(references_map)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Reference {reference_id} deleted from topic {topic_name}"
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                                    "message": f"Error deleting reference: {str(e)}"
                }
            )

# Assessment caching endpoints
@router.post("/assessment/cache-result/")
async def cache_assessment_result(cache_data: dict):
    """Cache an assessment result for future retrieval."""
    try:
        # Validate required fields
        if 'id' not in cache_data:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Missing required field: id"
                }
            )
        
        # Save to cache
        cache_path = save_assessment_cache(cache_data)
        if cache_path:
            return JSONResponse(content={
                "success": True,
                "message": f"Assessment result cached successfully",
                "cache_id": cache_data['id'],
                "cache_path": cache_path
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Failed to save assessment to cache"
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error caching assessment result: {str(e)}"
            }
        )

@router.get("/assessment/cached-results/")
async def list_cached_assessments():
    """List all cached assessment results."""
    try:
        cache_map = load_assessment_cache_map()
        cached_assessments = []
        
        for cache_id, cache_entry in cache_map.items():
            try:
                # Verify file exists
                json_file = cache_entry.get('json_file')
                if json_file and os.path.exists(json_file):
                    cached_assessments.append({
                        "id": cache_id,
                        "type": cache_entry.get('type', 'assessment'),
                        "topic": cache_entry.get('topic', 'Unknown Topic'),
                        "createdAt": cache_entry.get('created_at', ''),
                        "casesCount": cache_entry.get('cases_count', 0),
                        "competenciesCount": cache_entry.get('competencies_count', 0),
                        "coveragePercentage": cache_entry.get('coverage_percentage', 0)
                    })
            except Exception as e:
                print(f"Error processing cache entry for {cache_id}: {e}")
                continue
        
        return JSONResponse(content=cached_assessments)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error listing cached assessments: {str(e)}"
            }
        )

@router.get("/assessment/cached-result/{cache_id}/")
async def get_cached_assessment(cache_id: str):
    """Get a specific cached assessment result."""
    try:
        cached_data = get_assessment_cache(cache_id)
        if not cached_data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Cached assessment with ID {cache_id} not found"
                }
            )
        
        return JSONResponse(content=cached_data)
        
    except Exception as e:
                return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error loading cached assessment: {str(e)}"
            }
        ) 