"""
Master Case Generator Service
Handles the generation of 13-part master case documents from case specifications
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel

class MasterCaseRequest(BaseModel):
    caseTitle: str
    scenario: str
    primaryCompetencies: List[str]
    reasoning: str
    setting: str
    abstractVariables: Optional[List[str]] = []
    emotionalLayer: Optional[str] = ""
    mysteryHook: Optional[str] = ""
    references: str  # Markdown text from reference context file
    topic_name: Optional[str] = None  # Topic name for folder organization

class MasterCaseResponse(BaseModel):
    success: bool
    case_document: Optional[str] = None
    saved_path: Optional[str] = None
    disease_name: Optional[str] = None
    message: str

# Master Case Generator prompt (adapted from v4)
MASTER_CASE_GENERATOR_PROMPT = """# 🧠 Master Case Generator v4.0 

You are an expert AI Medical Education Content Creator. Your function is to generate highly structured, clinically accurate, and engaging medical case documents for teaching purposes based on provided clinical references and case specifications.

**Core Objective:** Create a comprehensive case document with all 13 parts that serves as a rich grounding text for medical education. The case must be meticulously based on provided clinical references and current medical guidelines.

**CRITICAL INSTRUCTION:** You MUST generate all 13 parts in the exact formatting structure provided below. Follow the EXACT format and structure shown in the sample case.

---

## Input Data:
**Case Title:** {case_title}
**Clinical Scenario:** {scenario}
**Primary Competencies:** {competencies}
**Educational Reasoning:** {reasoning}
**Setting:** {setting}
**Abstract Variables:** {abstract_variables}
**Emotional Layer:** {emotional_layer}
**Mystery Hook:** {mystery_hook}

**Clinical References:**
{references}

---

## SAMPLE CASE FORMAT (Follow this EXACT structure and format):

{sample_case_format}

---

## Required Output Format:

Generate the complete case document with the following 13 parts, following the EXACT format shown in the sample above:

## **Master Clinical Case: [Disease Name]**
---

### **Part 1: Case Description**
**Patient Profile:**
**Chief Complaint:**
**History of Present Illness:**
**Key Risk Factors:**
**Relevant Review of Systems Snippet:**

### **Part 2: Primary Symptoms**
1. 
2. 
3. 
4. 
5. 

### **Part 3: Background Factors**
**Relevant Medical & Social History:**
**Potentially Distracting/Non-Contributory Information:**

### **Part 4: Physical Examination Checklist**
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 

### **Part 5: Lab Test Masterlist**
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 

### **Part 6: Information Gathering & Clue Unlocking**
**Key History Questions to Ask:**
**Expected Vital Signs:**
**Key Expected Physical Exam Findings & Their Significance:**

### **Part 7: Primary Diagnosis & Initial Reasoning**
**Most Likely Primary Diagnosis:**
**Reasoning Supporting This Diagnosis:**
**Initial Differentiation from Key Alternatives:**
**Suggested Concept Nodes for Diagnosis:**

### **Part 8: Differential Diagnoses & Differentiation**
**A) Plausible Differential Diagnoses (Should Be Considered):**
**B) Less Likely/Incorrect Differentials (Tempting but Ruled Out):**
**C) Rationale for Excluding Incorrect Differentials:**
**D) Key Differentiating Features for Plausible Differentials (vs. Primary Diagnosis):**

### **Part 9: Test Interpretation & Diagnostic Confirmation**
**A) Expected Positive/Confirmatory Test Results (for Primary Diagnosis):**
**B) Expected Results for Other Ordered/Considered Tests (Including Those Ruling Out Differentials):**
**Suggested Concept Nodes for Test Interpretation:**

### **Part 10: Final Diagnosis & Case Summary Feedback Points**
**Final Confirmed Diagnosis:**
**Key Evidence Summary Supporting Final Diagnosis:**
**Resolution of Differential Diagnoses:**
**Reflection on Case Challenges (if any):**

### **Part 11: Management & Treatment Plan – *[Disease Name]***
#### 🧪 Pre-Treatment & Baseline Investigations (Beyond Initial Diagnostics)
#### 🔁 Monitoring During & After Treatment
#### 💊 Structured Treatment Plan
#### 🛡️ Supportive Care & Preventive Measures
#### 📈 Prognosis & 📅 Long-Term Outlook

### **Part 12: OSCE Stations – *[Disease Name]***
#### 🔹 Station 1: Focused History Taking & Risk Assessment
#### 🔹 Station 2: Physical Examination Technique or Image Interpretation
#### 🔹 Station 3: Counseling & Management Explanation

### **Part 13: MCQs – *[Disease Name]***
#### ❓ MCQ 1: Focus on Classic Presentation / Key Diagnostic Feature
#### ❓ MCQ 2: Focus on Most Appropriate Initial Investigation or Gold Standard Test
#### ❓ MCQ 3: Focus on First-Line Treatment or Key Management Principle

---

**Instructions:**
1. Extract the disease name from the case title for use in part titles
2. Integrate the abstract variables, emotional layer, and mystery hook naturally throughout the case
3. Use the clinical references to ensure medical accuracy
4. Ensure the case addresses all provided competencies
5. Follow the exact formatting structure shown above
6. Include clinical reasoning throughout
7. Make the case engaging and educational

Generate the complete case document now:"""

async def call_gemini_api(prompt: str) -> str:
    """Call Google Gemini API with the given prompt"""
    try:
        from google import genai
        
        # Get API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise Exception("GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")
        
        # Initialize Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        print("Sending to Gemini API for master case generation...")
        
        # Send to Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                temperature=0.3,
                max_output_tokens=4000
            ),
        )
        
        return response.text.strip()
        
    except ImportError:
        raise Exception("Google GenAI SDK not installed. Please install with: pip install google-genai")
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

async def generate_master_case(request: MasterCaseRequest) -> MasterCaseResponse:
    """
    Generate a complete 13-part master case document from approved case details
    """
    try:
        # Load sample case format
        sample_case_path = Path("services/Bacterial Vaginosis - format sample.md")
        sample_case_format = ""
        if sample_case_path.exists():
            with open(sample_case_path, 'r', encoding='utf-8') as f:
                sample_case_format = f.read()
        else:
            print("⚠️ Warning: Sample case format file not found")
        
        # Format the prompt with input data
        formatted_prompt = MASTER_CASE_GENERATOR_PROMPT.format(
            case_title=request.caseTitle,
            scenario=request.scenario,
            competencies=", ".join(request.primaryCompetencies),
            reasoning=request.reasoning,
            setting=request.setting,
            abstract_variables=", ".join(request.abstractVariables) if request.abstractVariables else "None",
            emotional_layer=request.emotionalLayer or "None",
            mystery_hook=request.mysteryHook or "None",
            references=request.references,
            sample_case_format=sample_case_format
        )
        
        # Call Gemini API
        print(f"🚀 Generating master case for: {request.caseTitle}")
        response_text = await call_gemini_api(formatted_prompt)
        
        # Extract disease name from case title for filename
        disease_name = request.caseTitle.replace(" ", "_").replace("/", "_").replace("\\", "_")
        # Remove special characters
        disease_name = re.sub(r'[^\w\-_]', '', disease_name)
        
        # Create topic-specific directory structure
        case_docs_base_dir = Path("cache/case_docs")
        
        # If topic_name is provided, create a subfolder for it
        if hasattr(request, 'topic_name') and request.topic_name:
            # Sanitize topic name for folder
            topic_folder = request.topic_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            topic_folder = re.sub(r'[^\w\-_]', '', topic_folder)
            case_docs_dir = case_docs_base_dir / topic_folder
        else:
            case_docs_dir = case_docs_base_dir
        
        # Ensure the directory exists
        case_docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the case document
        case_file_path = case_docs_dir / f"{disease_name}.md"
        with open(case_file_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        print(f"✅ Master case saved: {case_file_path}")
        
        return MasterCaseResponse(
            success=True,
            case_document=response_text,
            saved_path=str(case_file_path),
            disease_name=disease_name,
            message=f"Master case document generated and saved as {disease_name}.md"
        )
        
    except Exception as e:
        print(f"❌ Error generating master case: {e}")
        return MasterCaseResponse(
            success=False,
            message=f"Error generating master case: {str(e)}"
        )

async def generate_multiple_master_cases(cases: List[Dict], references: str, topic_name: str = None) -> Dict:
    """
    Generate multiple master cases from a list of approved cases
    """
    generated_cases = []
    failed_cases = []
    
    for case in cases:
        try:
            # Create master case request
            master_case_request = MasterCaseRequest(
                caseTitle=case.get('caseTitle', ''),
                scenario=case.get('scenario', ''),
                primaryCompetencies=case.get('primaryCompetencies', []),
                reasoning=case.get('reasoning', ''),
                setting=case.get('setting', 'Ward'),
                abstractVariables=case.get('abstractVariables', []),
                emotionalLayer=case.get('emotionalLayer', ''),
                mysteryHook=case.get('mysteryHook', ''),
                references=references,
                topic_name=topic_name
            )
            
            # Generate the master case
            result = await generate_master_case(master_case_request)
            
            if result.success:
                generated_cases.append({
                    "case_title": case.get('caseTitle'),
                    "disease_name": result.disease_name,
                    "saved_path": result.saved_path,
                    "message": result.message
                })
            else:
                failed_cases.append({
                    "case_title": case.get('caseTitle'),
                    "error": result.message
                })
                
        except Exception as e:
            failed_cases.append({
                "case_title": case.get('caseTitle', 'Unknown'),
                "error": str(e)
            })
    
    return {
        "generated_cases": generated_cases,
        "failed_cases": failed_cases,
        "total_cases": len(cases),
        "successful_generations": len(generated_cases),
        "failed_generations": len(failed_cases)
    } 