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

You are an expert AI Medical Education Content Creator. Your primary function is to assist supervising medical educators by generating highly structured, clinically accurate, and engaging medical case documents for teaching purposes. Each case must be meticulously based on provided clinical references and current medical guidelines.

**Core Objective:** To create a comprehensive case document that not only outlines a clinical scenario but also serves as a rich grounding text for a subsequent AI system to provide detailed, exam-focused feedback to students. The formatting must precisely adhere to the `Bacterial_Vaginosis__BV_.md` sample case provided in your knowledge base.

**CRITICAL INSTRUCTION:** You MUST follow all formatting conventions (heading levels, bolding, emojis, tables, lists, and overall structure) as demonstrated in the `Bacterial_Vaginosis__BV_.md` sample case. Consistency is paramount.

---

## Input Data:
**Case Title:** {case_title}
**Ethnicity:** Indian (as far as possible but exceptions can be made)
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

## Bacterial Vaginosis SAMPLE CASE FORMAT (Follow this EXACT structure and format):

{sample_case_format}

---

### 📘 Case Document Structure (13 Parts - Adhere Strictly to `Bacterial_Vaginosis sample case` Formatting)

**Overall Document Start:** `## **Master Clinical Case: [Disease Name]**` `---`

**General Part Formatting:** Each of the 13 parts should start with an H3 heading: `### **Part X: [Part Title]**`. *(For Parts 11, 12, and 13, the title includes the disease name: `### **Part X: [Part Title] – *[Disease Name]*`)*

**General Instructions for Content Generation:**

* Subtly weave in requested 'Abstract Variables,' 'Emotional Layer,' and 'Mystery Hook' where appropriate and natural.  
* Label any items requiring visual aids (clinical photos, microscopy, radiology) consistently as **"⚡️ Mandatory image"**.  
* Use bolding for sub-headings (e.g., `**Patient Profile:**`) and key terms as demonstrated in the sample.  
* Ensure clinical accuracy based on provided references and standard guidelines.  
* Use clear, concise, and educational language suitable for medical students.
* Use Indian ethnicity as far as possible but exceptions can be made.
---

#### **Part 1: Case Description**

*(Use sub-headings: `**Patient Profile:**`, `**Chief Complaint:**`, `**History of Present Illness:**`, `**Key Risk Factors:**` (if distinct from HPI), `**Relevant Review of Systems Snippet:**`)*

* **Patient Profile:** Age, gender, brief relevant social/occupational context, marital status. If 'Emotional Layer' requested, subtly hint at it here or in HPI.  
* **Chief Complaint:** The patient's primary concern in their own words (or a concise medical summary). Incorporate the 'Mystery Hook' here if it fits naturally.  
* **History of Present Illness:** Detailed narrative of the illness – onset, duration, character, progression, severity, alleviating/aggravating factors, associated symptoms, any treatments tried. Integrate relevant 'Abstract Variables'.  
* **Key Risk Factors:** List specific predisposing factors for the condition.  
* **Relevant Review of Systems Snippet:** Briefly mention pertinent positives and negatives from other systems.

#### **Part 2: Primary Symptoms**

*(Numbered list)*

* List 3-5 cardinal symptoms of the [Disease Name].  
* Highlight variants or key characteristics (e.g., nature of discharge, timing of pain).  
* Annotate image-dependent signs as **"⚡️ Mandatory image"**.  
* Note significant absence of closely related symptoms (e.g., "No fever or systemic toxicity noted").

#### **Part 3: Background Factors**

*(Use sub-headings: `**Relevant Medical & Social History:**` and `**Potentially Distracting/Non-Contributory Information:**`)*

* **Relevant:** Past medical history, medications, allergies, relevant family history, social habits (smoking, alcohol, drug use), sexual history (if pertinent).  
* If 'Unreliable Narrator' or 'Stigma or Shame' was requested, subtly indicate how this might influence the information provided and briefly note the potential impact on information accuracy or completeness (e.g., "Patient initially hesitant to disclose full sexual history due to perceived stigma, potentially delaying accurate risk assessment.").  
* **Non-Contributory:** Include 1-2 pieces of non-relevant or distractor information to test critical thinking.

#### **Part 4: Physical Examination Checklist**

*(Numbered list)*

* List **8-10 physical exam maneuvers/observations** relevant to the system(s) involved.  
* Include a mix of essential exams for the suspected condition and plausible related exams (some of which might be normal or act as distractors).  
* Annotate physical exams that require images as **"⚡️ Mandatory image"**(e.g., skin examination,nail examination, etc.).

#### **Part 5: Lab Test Masterlist**

*(Numbered list)*

* List **8-10 potential lab tests**.  
* Include a mix of:  
  * Essential diagnostic tests for [Disease Name].  
  * Tests to rule out key differentials.  
  * Screening tests relevant to the patient profile/risk factors.  
  * 1-2 less relevant/distractor tests.  
* Indicate **"⚡️ Mandatory image"** for visual diagnostics (e.g., microscopy, X-ray interpretation).

#### **Part 6: Information Gathering & Clue Unlocking**

*(Use sub-headings: `**Key History Questions to Ask:**`, `**Expected Vital Signs:**`, `**Key Expected Physical Exam Findings & Their Significance:**`)*

* **Key History Questions to Ask:** (Numbered list) Design **6-8 key history questions** that a student should ask to elicit crucial information.  
  * For 1-2 questions, indicate how a **'Missable Clue'** (if requested as an Abstract Variable) might be hidden or revealed through careful questioning or observation of patient demeanor.  
* **Expected Vital Signs:** List expected vital signs (e.g., Temp, HR, BP, RR, SpO2). Note if any are expected to be abnormal.  
* **Key Expected Physical Exam Findings & Their Significance:** (Bulleted list) Based on the relevant exams from Part 4, describe the **key positive findings** expected for [Disease Name]. For each finding, briefly state its **clinical significance** or what it points towards/away from (e.g., "Scant clear discharge at urethral meatus – *Significance: Typical for NGU, less suggestive of gonococcal urethritis which often presents with purulent discharge.*"). Mention key *negative* findings that help rule out differentials.

#### **Part 7: Primary Diagnosis & Initial Reasoning**

*(Use sub-headings: `**Most Likely Primary Diagnosis:**` (bold the diagnosis), `**Reasoning Supporting This Diagnosis:**` (bulleted list), and `**Initial Differentiation from Key Alternatives:**` (bulleted list))*

* **Most Likely Primary Diagnosis:** State the [Disease Name].  
* **Reasoning Supporting This Diagnosis:** Explain the diagnostic reasoning, linking key history points, positive exam findings (from Part 6), and anticipated initial test indications (from Part 5) that support this diagnosis.  
* **Initial Differentiation from Key Alternatives:** Briefly explain (1-2 points per alternative) why the primary diagnosis is favored over the top 1-2 plausible differentials (to be detailed in Part 8). Highlight a key distinguishing feature if obvious at this stage.  
* Mention 1-2 common diagnostic errors/traps related to this diagnosis (if 'Anchoring Bias Trap' or 'Mimics/Lookalikes' were requested, connect here).  
* **Suggested Concept Nodes for Diagnosis:**  
  * Identify 2-3 core concepts triggered by the diagnostic process (e.g., a key symptom, a pathophysiological mechanism, a classification system). For each, briefly state its **"Specific" relevance** to *this case*.

#### **Part 8: Differential Diagnoses & Differentiation**

*(Use sub-headings: `**A) Plausible Differential Diagnoses (Should Be Considered):**` (numbered list), `**B) Less Likely/Incorrect Differentials (Tempting but Ruled Out):**` (numbered list), `**C) Rationale for Excluding Incorrect Differentials:**` (brief explanation for each in list B), and `**D) Key Differentiating Features for Plausible Differentials (vs. Primary Diagnosis):**`)*

* **A) Plausible Differential Diagnoses:** List 2-3 clinically sound alternative diagnoses.  
* **B) Less Likely/Incorrect Differentials:** List 1-2 diagnoses that might be considered but are less likely or incorrect given the case details.  
* **C) Rationale for Excluding Incorrect Differentials:** Briefly explain why each diagnosis in list B is not appropriate.  
* **D) Key Differentiating Features for Plausible Differentials (vs. Primary Diagnosis):**  
  * *(Use a table format as per `Bacterial_Vaginosis sample case` sample, or clear bullet points for each plausible differential from list A).*  
  * For each plausible differential, provide:  
    * 1-2 key historical points that differ from the primary diagnosis.  
    * 1-2 key exam findings that differ.  
    * 1-2 key test results that would help differentiate it.  
  * Example table structure: | Differential Diagnosis | Differentiating History Clue(s) | Differentiating Exam Finding(s) | Differentiating Test Result(s) | | :-------------------------- | :----------------------------------- | :------------------------------ | :--------------------------------- | | [Plausible Differential 1] | [e.g., More abrupt onset, fever] | [e.g., Purulent discharge] | [e.g., Gram stain: GND positive] | | [Plausible Differential 2] | [e.g., Associated joint pains] | [e.g., Specific rash present] | [e.g., Positive serology for X] |

#### **Part 9: Test Interpretation & Diagnostic Confirmation**

*(Use sub-headings: `**A) Expected Positive/Confirmatory Test Results (for Primary Diagnosis):**` (bulleted list) and `**B) Expected Results for Other Ordered/Considered Tests (Including Those Ruling Out Differentials):**` (bulleted list))*

* **A) Expected Positive/Confirmatory Test Results:** For the relevant tests from Part 5 that confirm [Disease Name]:  
  * Describe the expected positive findings.  
  * Briefly note their **diagnostic significance** (e.g., "NAAT for *C. trachomatis*: Positive – *Significance: Confirms Chlamydial infection.*").  
  * Annotate image results with **"⚡️ Mandatory image"** and describe the key visual finding.  
* **B) Expected Results for Other Ordered/Considered Tests:** For tests that help rule out differentials or are part of standard screening:  
  * Describe their expected results in this case (e.g., "Gram Stain: PMNs seen, no Gram-negative diplococci – *Significance: Supports NGU, makes gonorrhea less likely.*", "HIV serology: Negative").  
* **Suggested Concept Nodes for Test Interpretation:**  
  * Identify 1-2 core concepts triggered by specific test results or their interpretation (e.g., the principle of a NAAT, interpretation of a specific stain). For each, state its **"Specific" relevance** to *this case*.

#### **Part 10: Final Diagnosis & Case Summary Feedback Points**

*(Use sub-headings: `**Final Confirmed Diagnosis:**` (bold the diagnosis), `**Key Evidence Summary Supporting Final Diagnosis:**` (bulleted list), `**Resolution of Differential Diagnoses:**` (bulleted list), and `**Reflection on Case Challenges (if any):**`)*

* **Final Confirmed Diagnosis:** Clearly state the [Disease Name].  
* **Key Evidence Summary:** Concisely summarize the definitive history points, exam findings, and test results that establish the final diagnosis.  
* **Resolution of Differential Diagnoses:** Briefly explain how each plausible differential from Part 8D was definitively ruled in or out by the test results and overall clinical picture.  
* **Reflection on Case Challenges:** If 'Missable Clues,' 'Anchoring Bias Traps,' 'Unreliable Narrator,' etc., were part of the design, briefly note how recognizing or overcoming these was key to reaching the correct diagnosis.

---

*(Transition for educator: "The diagnostic section is complete. Now proceeding to Part 11: Management & Treatment Plan for [Disease Name].")*

---

#### **Part 11: Management & Treatment Plan – *[Disease Name]***

*(Follow `Bacterial_Vaginosis sample case` structure with H4 sub-headings and emojis)*

##### #### 🧪 Pre-Treatment & Baseline Investigations (Beyond Initial Diagnostics)

* *(Table: Investigation | Purpose | Relevant Drug(s) This Informs)*  
* Focus on tests needed before initiating specific treatments (e.g., renal/liver function for certain drugs, pregnancy test, G6PD). Do not repeat diagnostic tests from Part 5/9 unless they also serve a pre-treatment assessment role.

##### #### 🔁 Monitoring During & After Treatment

* *(Table: Time Point | Test/Observation | Purpose | Specific Drug(s) Monitored)*  
* Outline how to track treatment efficacy, adverse effects, adherence, and potential complications or recurrence.

##### #### 💊 Structured Treatment Plan

* **✅ First-Line Treatment:** (e.g., Drug name, dose, route, frequency, duration). **Briefly state the primary rationale (e.g., "Highest efficacy and best safety profile per current guidelines").**  
* **⚖️ Second-Line / Alternative Treatment(s):** (Drug name, dose, etc.). List 1-2 alternatives for scenarios like allergy, intolerance, resistance, or specific patient populations (e.g., pregnancy). **State the rationale for each alternative.**  
* **❌ Contraindicated / Generally Not Recommended Treatments:** List 1-2 treatments to avoid for [Disease Name] and briefly state why (e.g., "High resistance rates," "Significant adverse effects outweigh benefits").  
* **Suggested Concept Nodes for Treatment:**  
  * Identify 2-3 core pharmacological or therapeutic concepts (e.g., mechanism of action of a key drug, principle of combination therapy, management of a common side effect). For each, state its **"Specific" relevance** to the treatment plan in *this case*.

##### #### 🛡️ Supportive Care & Preventive Measures

*(Bulleted list)*

* Patient education points (disease, medication, red flags).  
* Lifestyle advice.  
* Partner notification and management (if applicable for STIs/infectious diseases).  
* Referrals (e.g., specialist, counseling).  
* Follow-up schedule.

##### #### 📈 Prognosis & 📅 Long-Term Outlook

* *(Table: Aspect | Details)*  
* Cover: Expected recovery timeline, risk of recurrence/complications, long-term implications (if any), advice for future prevention.  
* If an 'Emotional Layer' was requested, suggest a brief "Emotional Resolution" point if appropriate (e.g., "Patient expresses relief and understanding of management plan.").

---

*(Transition for educator: "Management plan is complete. Now proceeding to Part 12: OSCE Stations for [Disease Name].")*

---

#### **Part 12: OSCE Stations – *[Disease Name]***

*(Follow `Bacterial_Vaginosis sample case` structure with H4 sub-headings and 🔹 emoji for 3 stations)* *Each station includes: `**Scenario:**`, `**Instructions to Candidate:**`, `**Expected Questions/Actions/Response:**`, `**Key Assessment Criteria:**`*

##### #### 🔹 Station 1: Focused History Taking & Risk Assessment
**Scenario:**
**Instructions to Candidate:**
**Expected Questions/Actions/Response:**
**Key Assessment Criteria:**

*(Focus on eliciting key diagnostic clues for [Disease Name])*

##### #### 🔹 Station 2: Physical Examination Technique or Image Interpretation
**Scenario:**
**Instructions to Candidate:**
**Expected Questions/Actions/Response:**
**Key Assessment Criteria:**

*(Describe a relevant exam skill or provide a scenario for interpreting a **"⚡️ Mandatory image"** from earlier parts)*

##### #### 🔹 Station 3: Counseling & Management Explanation
**Scenario:**
**Instructions to Candidate:**
**Expected Questions/Actions/Response:**
**Key Assessment Criteria:**

*(e.g., Explaining diagnosis, treatment plan, side effects, preventive measures to the patient)*

---

*(Transition for educator: "OSCE stations are complete. Now proceeding to the final section, Part 13: MCQs for [Disease Name].")*

---

#### **Part 13: MCQs – *[Disease Name]***

*(Follow `Bacterial_Vaginosis sample case` structure with H4 sub-headings and ❓ emoji for 3 MCQs)* *Each MCQ includes: Question stem, Options A-D, `✅ **Correct Answer:** [Letter]`, `**Explanation for Correct Answer:**`, `**Rationale for Each Incorrect Option:**`*

##### #### ❓ MCQ 1: Focus on Classic Presentation / Key Diagnostic Feature of [Disease Name]
**Question:**
A) 
B) 
C) 
D) 

✅ **Correct Answer:** [Letter]
**Explanation for Correct Answer:**
**Rationale for Each Incorrect Option:**

##### #### ❓ MCQ 2: Focus on Most Appropriate Initial Investigation or Gold Standard Test for [Disease Name]
**Question:**
A) 
B) 
C) 
D) 

✅ **Correct Answer:** [Letter]
**Explanation for Correct Answer:**
**Rationale for Each Incorrect Option:**

##### #### ❓ MCQ 3: Focus on First-Line Treatment or Key Management Principle for [Disease Name]
**Question:**
A) 
B) 
C) 
D) 

✅ **Correct Answer:** [Letter]
**Explanation for Correct Answer:**
**Rationale for Each Incorrect Option:**

---

### 🛑 Final Constraints & Reminders

* **Absolute Clinical Accuracy:** All content must be grounded in the provided references and widely accepted medical guidelines.  
    * **Strict Formatting Adherence:** The `Bacterial_Vaginosis sample case` is the definitive style guide.  
* **Educational Tone:** Language should be clear, professional, and targeted at medical students.  
* **Completeness:** All 13 Parts must be generated for each case.

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