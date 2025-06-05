"""
Tables router for table extraction and processing
"""

import os
import shutil
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/tables", tags=["tables"])

@router.post("/extract-json/")
async def extract_table_json(
    file: UploadFile = File(...)
):
    """
    Extract tables from uploaded file and convert to JSON using Gemini API.
    Returns clean JSON data structure.
    """
    try:
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
        
        prompt = f"""Convert the following markdown table(s) to this specific JSON format:
{{
  "topics": [
    {{
      "topic": "T1", 
      "competencies": [
        {{"code": "GM6.22", "description": "Demonstrate a non-judgmental attitude...", "column3": "A", "column4": "SH", "column5": "Y", "column6": "Bedside clinic..."}},
        {{"code": "GM6.23", "description": "Another competency...", "column3": "B", "column4": "SH", "column5": "N", "column6": "Lab session..."}}
      ]
    }}
  ]
}}

Instructions:
- Group rows by topic (first column or most appropriate grouping)
- Each competency should be an object containing ALL columns from that row
- Use column headers as keys, or if no headers use: "code", "description", "column3", "column4", etc.
- Preserve all data from each row - nothing should be lost
- Use the actual text content from the table
- Return only the JSON, no explanations or markdown formatting

Markdown tables:
{combined_markdown}

Return only the JSON in the specified format with full row objects."""

        print("Sending to Gemini API for JSON conversion...")
        
        # Send to Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
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
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {json_response}")
            # Fallback: return structured data in the requested format with full row objects
            topics = []
            for t, (_, table) in zip(tables_markdown, enumerate(conv_res.document.tables)):
                table_df = table.export_to_dataframe()
                if not table_df.empty:
                    # Group all rows under a single topic or create multiple topics
                    competencies = []
                    
                    # Get column names or create default ones
                    column_names = list(table_df.columns) if table_df.columns.tolist() != list(range(len(table_df.columns))) else [f"column{i+1}" for i in range(len(table_df.columns))]
                    
                    # Convert each row to a competency object
                    for index, row in table_df.iterrows():
                        row_obj = {}
                        for col_idx, col_name in enumerate(column_names):
                            if col_idx < len(row):
                                value = row.iloc[col_idx]
                                row_obj[col_name] = str(value) if not pd.isna(value) else ""
                            else:
                                row_obj[col_name] = ""
                        
                        # Only add non-empty rows
                        if any(v.strip() for v in row_obj.values() if v):
                            competencies.append(row_obj)
                    
                    # Create a topic entry
                    if competencies:
                        # Use first row's first column as topic if available, otherwise generic name
                        topic_name = competencies[0].get(column_names[0], f"Table_{t+1}") if competencies else f"Table_{t+1}"
                        topics.append({
                            "topic": topic_name,
                            "competencies": competencies
                        })
            
            parsed_json = {"topics": topics}
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        processing_time = time.time() - start_time
        
        print(f"Processing completed in {processing_time:.2f}s")
        print(f"Found {len(tables_markdown)} table(s)")
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "tables_found": len(tables_markdown),
            "processing_time": f"{processing_time:.2f}s",
            "json_data": parsed_json
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

@router.post("/process/")
async def process_table(
    file: UploadFile = File(...),
    generate_csv: bool = Form(True),
    generate_html: bool = Form(True),
    generate_markdown: bool = Form(True)
):
    """
    Process a table image using Docling to extract tables and generate various formats.
    Based on the docling table export example.
    """
    try:
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
        output_dir = table_output_dir / f"{doc_filename}_{int(time.time())}"
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