"""
Assessment router for case generation and assessment management
"""

import os
import json
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Import services
from services.master_case_generator import MasterCaseRequest, MasterCaseResponse, generate_master_case
from services.case_management import case_manager

router = APIRouter(prefix="/api/assessment", tags=["assessment"])

# Pydantic models
class Competency(BaseModel):
    number: str
    competency: str
    teaching_methods: List[str]
    assessment_methods: List[str]

class TopicData(BaseModel):
    topic: str
    competencies: List[Competency]

class CompetencyGroup(BaseModel):
    groupName: str
    competencyNumbers: List[str]
    theme: str

class RecommendedCase(BaseModel):
    caseTitle: str
    scenario: str
    primaryCompetencies: List[str]
    reasoning: str
    setting: Optional[str] = None

class CoverageSummary(BaseModel):
    competenciesCovered: List[str]
    competenciesNotCovered: List[str]
    coveragePercentage: float

class Recommendation(BaseModel):
    totalCases: int
    rationale: str
    needsRevision: bool
    revisionNotes: Optional[str] = None

class CaseGenerationResponse(BaseModel):
    topic: str
    totalCompetencies: int
    competencyGroups: List[CompetencyGroup]
    recommendedCases: List[RecommendedCase]
    coverageSummary: CoverageSummary
    recommendation: Recommendation

class SelectedTopicRequest(BaseModel):
    selected_topic: TopicData

class AdditionalCasesRequest(BaseModel):
    original_topic: TopicData
    current_cases: List[RecommendedCase]
    revision_notes: str
    missing_competencies: List[str]

class AdditionalCasesResponse(BaseModel):
    new_cases: List[RecommendedCase]
    updated_coverage: Optional[CoverageSummary] = None
    rationale: str

# Models imported from services

# Case generation prompt
CASE_GENERATION_PROMPT = """# Medical Case Generation Planning

You are an expert medical educator tasked with determining the optimal clinical cases needed to cover all competencies for a medical topic.

## Input Topic and Competencies:
{topic_data}

## Instructions:

### Step 1: Analyze Competencies
- Identify key themes and clinical concepts
- Group related competencies by disease, process, or skill type
- Note knowledge vs skills vs communication focus

### Step 2: Design Cases
- Create distinct clinical scenarios that effectively teach competency groups
- Ensure variety in severity, etiology, acute/chronic, and settings
- Aim for minimum cases with maximum coverage

### Step 3: Verify Coverage
- Ensure all competencies are addressed (primary or secondary)
- Check for gaps or redundancy

## Required Output Format:
Return ONLY a valid JSON object matching this exact schema:

{{
  "topic": "string",
  "totalCompetencies": integer,
  "competencyGroups": [
    {{
      "groupName": "string",
      "competencyNumbers": ["GM5.10", "GM5.11"],
      "theme": "string describing common theme"
    }}
  ],
  "recommendedCases": [
    {{
      "caseTitle": "string",
      "scenario": "brief patient presentation description",
      "primaryCompetencies": ["GM5.10", "GM5.11"],
      "reasoning": "why this case addresses these competencies",
      "setting": "Outpatient|ED|Ward|ICU"
    }}
  ],
  "coverageSummary": {{
    "competenciesCovered": ["GM5.10", "GM5.11"],
    "competenciesNotCovered": ["GM5.12"],
    "coveragePercentage": 90.5
  }},
  "recommendation": {{
    "totalCases": 3,
    "rationale": "brief explanation of case selection strategy",
    "needsRevision": false,
    "revisionNotes": "optional notes if revision needed"
  }}
}}

IMPORTANT: Respond with valid JSON only. No additional text, explanations, or markdown formatting.

INPUT DATA:
{topic_data}

OUTPUT (JSON only):"""

# Additional cases generation prompt
ADDITIONAL_CASES_PROMPT = """# Generate Additional Assessment Cases

You are tasked with generating additional clinical cases to address specific competency coverage gaps identified in an initial assessment.

## Context:
**Topic:** {topic}
**Existing Cases:** {existing_cases}
**Missing Coverage:** {revision_notes}
**Uncovered Competencies:** {missing_competencies}

## Task:
Generate ONLY the additional cases needed to address the missing competencies. Do not recreate existing cases.

## Requirements:
1. Focus specifically on the uncovered competencies: {missing_competencies}
2. Address the gaps mentioned in: {revision_notes}
3. Ensure new cases complement existing ones without redundancy
4. Create diverse clinical scenarios (different settings, presentations, demographics)

## Output Format:
Return ONLY a valid JSON object with this exact schema:

{{
  "new_cases": [
    {{
      "caseTitle": "string",
      "scenario": "brief patient presentation description",
      "primaryCompetencies": ["competency codes that this case addresses"],
      "reasoning": "how this case specifically addresses the missing competencies",
      "setting": "Outpatient|ED|Ward|ICU"
    }}
  ],
  "updated_coverage": {{
    "competenciesCovered": ["all competencies covered by original + new cases"],
    "competenciesNotCovered": ["remaining uncovered competencies"],
    "coveragePercentage": 95.5
  }},
  "rationale": "brief explanation of how these additional cases address the gaps"
}}

IMPORTANT: 
- Generate ONLY new cases that address missing competencies
- Do not repeat or modify existing cases
- Respond with valid JSON only, no additional text

INPUT DATA:
Topic: {topic}
Missing Competencies: {missing_competencies}
Revision Notes: {revision_notes}

OUTPUT (JSON only):"""

# Master Case Generator prompt (adapted from v4)
MASTER_CASE_GENERATOR_PROMPT = """# 🧠 Master Case Generator v4.0 

You are an expert AI Medical Education Content Creator. Your function is to generate highly structured, clinically accurate, and engaging medical case documents for teaching purposes based on provided clinical references and case specifications.

**Core Objective:** Create a comprehensive case document with all 13 parts that serves as a rich grounding text for medical education. The case must be meticulously based on provided clinical references and current medical guidelines.

**CRITICAL INSTRUCTION:** You MUST generate all 13 parts in the exact formatting structure provided below.

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

## Required Output Format:

Generate the complete case document with the following 13 parts:

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

# Master Case Generator prompt (adapted from v4)
MASTER_CASE_GENERATOR_PROMPT = """# 🧠 Master Case Generator v4.0 

You are an expert AI Medical Education Content Creator. Your function is to generate highly structured, clinically accurate, and engaging medical case documents for teaching purposes based on provided clinical references and case specifications.

**Core Objective:** Create a comprehensive case document with all 13 parts that serves as a rich grounding text for medical education. The case must be meticulously based on provided clinical references and current medical guidelines.

**CRITICAL INSTRUCTION:** You MUST generate all 13 parts in the exact formatting structure provided below.

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

## Required Output Format:

Generate the complete case document with the following 13 parts:

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
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY not found in environment variables. Please add it to your .env file."
            )
        
        # Initialize Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        print("Sending to Gemini API for case generation...")
        
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
        raise HTTPException(
            status_code=500,
            detail="Google GenAI SDK not installed. Please install with: pip install google-genai"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(e)}"
        )

@router.post("/generate-cases", response_model=CaseGenerationResponse)
async def generate_cases(request: SelectedTopicRequest):
    """
    Generate recommended cases for a selected topic and its competencies
    """
    try:
        # Format topic data for the prompt
        topic_data = {
            "topic": request.selected_topic.topic,
            "competencies": [
                {
                    "number": comp.number,
                    "competency": comp.competency,
                    "teaching_methods": comp.teaching_methods,
                    "assessment_methods": comp.assessment_methods
                }
                for comp in request.selected_topic.competencies
            ]
        }
        
        # Format the prompt
        formatted_prompt = CASE_GENERATION_PROMPT.format(
            topic_data=json.dumps(topic_data, indent=2)
        )
        
        # Call Gemini API
        response_text = await call_gemini_api(formatted_prompt)
        
        # Clean up response
        json_response = response_text.strip()
        
        # Try to clean up any potential markdown formatting
        if json_response.startswith("```json"):
            json_response = json_response.replace("```json", "").replace("```", "").strip()
        elif json_response.startswith("```"):
            json_response = json_response.replace("```", "").strip()
        
        # Parse and validate JSON
        try:
            parsed_response = json.loads(json_response)
            
            # Validate required fields
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a JSON object")
            
            required_fields = ["topic", "totalCompetencies", "competencyGroups", 
                             "recommendedCases", "coverageSummary", "recommendation"]
            
            for field in required_fields:
                if field not in parsed_response:
                    raise ValueError(f"Missing required field: {field}")
            
            # Additional validation
            if not isinstance(parsed_response["competencyGroups"], list):
                parsed_response["competencyGroups"] = []
            
            if not isinstance(parsed_response["recommendedCases"], list):
                parsed_response["recommendedCases"] = []
            
            # Validate coverage summary
            coverage = parsed_response.get("coverageSummary", {})
            if "competenciesCovered" not in coverage:
                coverage["competenciesCovered"] = []
            if "competenciesNotCovered" not in coverage:
                coverage["competenciesNotCovered"] = []
            if "coveragePercentage" not in coverage:
                coverage["coveragePercentage"] = 0.0
            
            # Validate recommendation
            recommendation = parsed_response.get("recommendation", {})
            if "totalCases" not in recommendation:
                recommendation["totalCases"] = len(parsed_response["recommendedCases"])
            if "rationale" not in recommendation:
                recommendation["rationale"] = "Case selection based on competency analysis"
            if "needsRevision" not in recommendation:
                recommendation["needsRevision"] = False
            
            print(f"✅ Successfully generated {len(parsed_response['recommendedCases'])} cases for topic: {parsed_response['topic']}")
            
            return JSONResponse(content=parsed_response)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ JSON parsing/validation error: {e}")
            print(f"Response was: {json_response[:500]}...")
            
            # Create fallback response
            all_competency_numbers = [comp.number for comp in request.selected_topic.competencies]
            
            fallback_response = {
                "topic": request.selected_topic.topic,
                "totalCompetencies": len(request.selected_topic.competencies),
                "competencyGroups": [
                    {
                        "groupName": "General Competencies",
                        "competencyNumbers": all_competency_numbers,
                        "theme": "All competencies grouped together due to parsing error"
                    }
                ],
                "recommendedCases": [
                    {
                        "caseTitle": f"General {request.selected_topic.topic} Case",
                        "scenario": f"A comprehensive case covering {request.selected_topic.topic} competencies",
                        "primaryCompetencies": all_competency_numbers,
                        "reasoning": "Fallback case created due to AI response parsing error",
                        "setting": "Ward"
                    }
                ],
                "coverageSummary": {
                    "competenciesCovered": all_competency_numbers,
                    "competenciesNotCovered": [],
                    "coveragePercentage": 100.0
                },
                "recommendation": {
                    "totalCases": 1,
                    "rationale": "Fallback recommendation due to AI response parsing error",
                    "needsRevision": True,
                    "revisionNotes": f"AI response parsing failed: {str(e)}"
                }
            }
            
            return JSONResponse(content=fallback_response)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating cases: {str(e)}"
        )

# Example usage endpoint for testing
@router.post("/test-generate-cases")
async def test_generate_cases():
    """Test endpoint using the provided liver disease data"""
    
    # Use the liver disease data from the attached file
    test_topic = TopicData(
        topic="Liver Disease",
        competencies=[
            Competency(
                number="GM5.10",
                competency="Generate a differential diagnosis and prioritize based on clinical features that suggest a specific aetiology for the presenting symptom in patient with liver disease",
                teaching_methods=["Bedside clinic", "SGT"],
                assessment_methods=["Long/short case", "Documentation in Journal"]
            ),
            Competency(
                number="GM5.11",
                competency="Choose and interpret appropriate diagnostic tests including: CBC, bilirubin, liver function tests, Hepatitis serology and ascitic fluid examination in patient with liver diseases",
                teaching_methods=["Bedside clinic", "SGT", "Tutorial"],
                assessment_methods=["OSCE", "Viva Voce"]
            ),
            Competency(
                number="GM5.12",
                competency="Enumerate the indications for ultrasound and other Imaging studies including MRCP and ERCP and describe the findings in liver disease",
                teaching_methods=["Bedside clinic", "SGT", "Tutorial"],
                assessment_methods=["Application based question", "Viva voce"]
            )
        ]
    )
    
    request = SelectedTopicRequest(selected_topic=test_topic)
    return await generate_cases(request) 

@router.post("/generate-additional-cases", response_model=AdditionalCasesResponse)
async def generate_additional_cases(request: AdditionalCasesRequest):
    """
    Generate additional cases to address specific competency coverage gaps
    """
    try:
        # Format existing cases for the prompt
        existing_cases_summary = []
        for case in request.current_cases:
            existing_cases_summary.append({
                "title": case.caseTitle,
                "competencies": case.primaryCompetencies,
                "setting": case.setting
            })
        
        # Format the prompt
        formatted_prompt = ADDITIONAL_CASES_PROMPT.format(
            topic=request.original_topic.topic,
            existing_cases=json.dumps(existing_cases_summary, indent=2),
            revision_notes=request.revision_notes,
            missing_competencies=", ".join(request.missing_competencies)
        )
        
        # Call Gemini API
        response_text = await call_gemini_api(formatted_prompt)
        
        # Clean up response
        json_response = response_text.strip()
        
        # Try to clean up any potential markdown formatting
        if json_response.startswith("```json"):
            json_response = json_response.replace("```json", "").replace("```", "").strip()
        elif json_response.startswith("```"):
            json_response = json_response.replace("```", "").strip()
        
        # Parse and validate JSON
        try:
            parsed_response = json.loads(json_response)
            
            # Validate required fields
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a JSON object")
            
            required_fields = ["new_cases", "rationale"]
            for field in required_fields:
                if field not in parsed_response:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure new_cases is a list
            if not isinstance(parsed_response["new_cases"], list):
                parsed_response["new_cases"] = []
            
            # Calculate updated coverage if not provided
            if "updated_coverage" not in parsed_response or not parsed_response["updated_coverage"]:
                # Combine all competencies from original + new cases
                all_covered_competencies = set()
                for case in request.current_cases:
                    all_covered_competencies.update(case.primaryCompetencies)
                
                for new_case in parsed_response["new_cases"]:
                    if "primaryCompetencies" in new_case:
                        all_covered_competencies.update(new_case["primaryCompetencies"])
                
                # Get all topic competencies
                all_topic_competencies = [comp.number for comp in request.original_topic.competencies]
                remaining_uncovered = [comp for comp in all_topic_competencies if comp not in all_covered_competencies]
                
                coverage_percentage = (len(all_covered_competencies) / len(all_topic_competencies)) * 100 if all_topic_competencies else 100
                
                parsed_response["updated_coverage"] = {
                    "competenciesCovered": list(all_covered_competencies),
                    "competenciesNotCovered": remaining_uncovered,
                    "coveragePercentage": round(coverage_percentage, 1)
                }
            
            print(f"✅ Successfully generated {len(parsed_response['new_cases'])} additional cases for topic: {request.original_topic.topic}")
            
            return JSONResponse(content=parsed_response)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ JSON parsing/validation error in additional cases: {e}")
            print(f"Response was: {json_response[:500]}...")
            
            # Create fallback response with one generic additional case
            fallback_response = {
                "new_cases": [
                    {
                        "caseTitle": f"Additional {request.original_topic.topic} Case",
                        "scenario": f"A comprehensive case designed to address missing {request.original_topic.topic} competencies",
                        "primaryCompetencies": request.missing_competencies[:3],  # Take first 3 missing
                        "reasoning": "Fallback case created to address coverage gaps due to AI response parsing error",
                        "setting": "Ward"
                    }
                ],
                "updated_coverage": {
                    "competenciesCovered": [],
                    "competenciesNotCovered": request.missing_competencies,
                    "coveragePercentage": 75.0
                },
                "rationale": f"Fallback additional case due to AI response parsing error: {str(e)}"
            }
            
            return JSONResponse(content=fallback_response)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in generate_additional_cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating additional cases: {str(e)}"
        )

@router.post("/generate-master-case", response_model=MasterCaseResponse)
async def generate_master_case_endpoint(request: MasterCaseRequest):
    """
    Generate a complete 13-part master case document from approved case details
    """
    return await generate_master_case(request)

@router.post("/generate-master-cases-from-assessment")
async def generate_master_cases_from_assessment_endpoint(request: dict):
    """
    Generate master case documents from approved assessment cases.
    Expects: {topic_name: str, approved_cases: list, original_topic_data: dict}
    """
    from routers.tables import sanitize_topic_name
    
    topic_name = request.get('topic_name')
    approved_cases = request.get('approved_cases', [])
    original_topic_data = request.get('original_topic_data', {})
    
    # Sanitize topic name to match how references are stored
    sanitized_topic_name = sanitize_topic_name(topic_name) if topic_name else None
    
    result = await case_manager.generate_master_cases_from_assessment(
        sanitized_topic_name, approved_cases, original_topic_data
    )
    
    if result["success"]:
        return JSONResponse(content=result)
    else:
        return JSONResponse(
            status_code=400 if "Missing required fields" in result["message"] else 500,
            content=result
        )