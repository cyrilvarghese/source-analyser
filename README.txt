===============================================================================
                          PDF CHAPTER EXTRACTOR TOOLS
===============================================================================

A simple collection of tools to extract specific pages or chapters from PDF 
files. Perfect for splitting large textbooks into smaller, manageable sections.

===============================================================================
WHAT DOES THIS TOOL DO?
===============================================================================

This toolkit helps you:
- Extract specific pages from any PDF (e.g., pages 10-20)
- Split large PDFs into topic-based folders
- Organize chapters from medical textbooks, manuals, or any structured document
- Batch process hundreds of chapters automatically

===============================================================================
QUICK START GUIDE
===============================================================================

STEP 1: SET UP YOUR ENVIRONMENT

For Windows Users:
    Open Command Prompt or PowerShell and run:
    python -m venv crop-file
    crop-file\Scripts\activate
    pip install PyPDF2

For Mac/Linux Users:
    Open Terminal and run:
    python -m venv crop-file
    source crop-file/bin/activate
    pip install PyPDF2

STEP 2: DOWNLOAD THE SCRIPTS
Save these files in your working folder:
- pdf_cropper.py
- extract_sections_v2.py
- Your PDF file
- Your JSON configuration file (if using bulk extraction)

STEP 3: CHOOSE YOUR TOOL

===============================================================================
TOOL OPTIONS
===============================================================================

OPTION 1: EXTRACT SPECIFIC PAGES (SIMPLE)
Use Case: "I want pages 50-75 from this PDF"

Command:
    python pdf_cropper.py my_textbook.pdf -s 50 -e 75

Result: Creates my_textbook_cropped.pdf with pages 50-75

OPTION 2: BULK CHAPTER EXTRACTION (ADVANCED)
Use Case: "I want to split this medical textbook into organized topic folders"

Command:
    python extract_sections_v2.py topic-data2.json harrison_textbook.pdf -o extracted_chapters

Result: Creates organized folders like this:
    extracted_chapters/
    ├── 01_Heart_failure/
    │   ├── Electrolytes_Acid-Base_Balance.pdf
    │   ├── Infective_Endocarditis.pdf
    │   └── Congestive_Heart_Failure_and_Cor_Pulmonale.pdf
    ├── 02_Pneumonia/
    │   ├── Sepsis_and_Septic_Shock.pdf
    │   └── Pneumonia_and_Lung_Abscess.pdf
    └── 03_Diabetes_Mellitus/
        ├── Diabetic_Ketoacidosis_and_Hyperosmolar_Coma.pdf
        └── Diabetes_Mellitus.pdf

===============================================================================
CREATING CONFIGURATION FILES WITH AI
===============================================================================

WHY USE AI FOR CONFIGURATION?
Creating the JSON configuration file manually for large textbooks (500+ pages) 
would be extremely time-consuming. Instead, you can use AI language models to 
help generate the configuration automatically!

METHOD 1: USING LLM WITH TABLE OF CONTENTS
Best for: Textbooks with clear table of contents

Steps:
1. Extract/photograph the table of contents from your PDF
2. Use ChatGPT, Claude, or similar LLM with this prompt:

"I have a medical textbook and want to organize chapters by clinical topics. 
Please create a JSON configuration file in this format:

{
    "topics": [
        {
            "topic": "Heart failure",
            "chapters": [
                {
                    "title": "Chapter Title",
                    "from": start_page,
                    "to": end_page
                }
            ]
        }
    ]
}

Here's my table of contents:
[Paste your table of contents here]

Please group related chapters under appropriate clinical topics like 
'Heart failure', 'Diabetes', 'Infectious Diseases', etc."

Example Result: The AI will generate a properly formatted JSON file with 
logical topic groupings.

METHOD 2: USING LLM WITH INDEX/CHAPTER LIST
Best for: When you have a chapter index or detailed outline

Prompt Template:
"Create a JSON configuration for extracting PDF chapters. Group these 
chapters by medical specialty/topic:

Chapter 1: Introduction to Medicine (Pages 1-25)
Chapter 2: Physical Examination (Pages 26-50)
Chapter 15: Heart Failure (Pages 300-325)
Chapter 16: Myocardial Infarction (Pages 326-350)
[... your chapter list ...]

Format as JSON with topics like 'Cardiology', 'Endocrinology', etc."

METHOD 3: AI-ASSISTED PAGE NUMBER FINDING
For complex textbooks: Use AI to help identify relevant page ranges

Prompt:
"I have a 1000-page medical textbook. Help me find all chapters related to:
- Heart disease and cardiology
- Diabetes and endocrinology  
- Infectious diseases
- Kidney disease

Based on this table of contents: [paste contents]
Create a JSON file grouping related chapters by medical topic."

===============================================================================
REAL-WORLD EXAMPLES
===============================================================================

EXAMPLE 1: EXTRACT ONE CHAPTER
Scenario: You want Chapter 5 (pages 100-150) from a textbook
Command: python pdf_cropper.py textbook.pdf -s 100 -e 150 -o chapter_5.pdf
What you get: A file called chapter_5.pdf with just those pages

EXAMPLE 2: MEDICAL STUDENT STUDY GUIDE
Scenario: You have a 1000-page medical textbook and want each topic in 
separate folders
Command: python extract_sections_v2.py medical_topics.json harrison_medicine.pdf -o study_materials
What you get: Organized folders for each medical condition with relevant chapters

EXAMPLE 3: COURSE MATERIAL ORGANIZATION
Scenario: Split a large course manual into weekly topics
Command: python extract_sections_v2.py course_structure.json course_manual.pdf -o weekly_readings

===============================================================================
SETTING UP YOUR CONFIGURATION FILE
===============================================================================

For bulk extraction, you need a JSON file that tells the tool what to extract:

SIMPLE JSON TEMPLATE:
{
    "topics": [
        {
            "topic": "Introduction to Medicine",
            "chapters": [
                {
                    "title": "History Taking",
                    "from": 1,
                    "to": 25
                },
                {
                    "title": "Physical Examination",
                    "from": 26,
                    "to": 50
                }
            ]
        },
        {
            "topic": "Cardiology",
            "chapters": [
                {
                    "title": "Heart Failure",
                    "from": 200,
                    "to": 225
                }
            ]
        }
    ]
}

HOW TO CREATE YOUR OWN:
1. Open a text editor (Notepad, TextEdit, or any editor)
2. Copy the template above
3. Replace the example data with your actual:
   - Topic names
   - Chapter titles  
   - Page numbers (start and end)
4. Save as your_topics.json

===============================================================================
COMMAND REFERENCE
===============================================================================

BASIC PAGE EXTRACTION
Command: python pdf_cropper.py [PDF_FILE] [OPTIONS]

Options:
-s 10           Start from page 10
-e 50           End at page 50  
-o filename.pdf Save with custom name

Examples:
# Extract pages 1-100
python pdf_cropper.py book.pdf -e 100

# Extract pages 50-75, save as "chapter3.pdf"
python pdf_cropper.py book.pdf -s 50 -e 75 -o chapter3.pdf

# Extract from page 200 to end
python pdf_cropper.py book.pdf -s 200

BULK CHAPTER EXTRACTION
Command: python extract_sections_v2.py [JSON_FILE] [PDF_FILE] [OPTIONS]

Options:
-o folder_name  Save to specific folder

Examples:
# Basic extraction
python extract_sections_v2.py topics.json textbook.pdf

# Save to specific folder
python extract_sections_v2.py topics.json textbook.pdf -o my_chapters

# Medical textbook example
python extract_sections_v2.py medical_topics.json harrison.pdf -o medical_study_guide

===============================================================================
UNDERSTANDING THE OUTPUT
===============================================================================

SINGLE FILE EXTRACTION:
Input: medical_textbook.pdf
Command: python pdf_cropper.py medical_textbook.pdf -s 100 -e 150
Output: medical_textbook_cropped.pdf (contains pages 100-150)

BULK EXTRACTION:
Input: JSON config + large PDF
Output: Organized folder structure with numbered topics

your_output_folder/
├── 01_Heart_Disease/
│   ├── Heart_Failure.pdf
│   ├── Myocardial_Infarction.pdf
│   └── Arrhythmias.pdf
├── 02_Respiratory_Disease/
│   ├── Pneumonia.pdf
│   └── COPD.pdf
└── 03_Endocrinology/
    ├── Diabetes.pdf
    └── Thyroid_Disorders.pdf

===============================================================================
TROUBLESHOOTING
===============================================================================

PROBLEM: "Command not found" or "python not recognized"
SOLUTION: Install Python from python.org and make sure it's added to your 
system PATH

PROBLEM: "File not found"
SOLUTION: 
- Check that your PDF file is in the same folder as the script
- Use the full file path: C:\Users\YourName\Documents\textbook.pdf

PROBLEM: "Permission denied"
SOLUTION: 
- Make sure the PDF isn't open in another program
- Check that you have write permissions in the output folder

PROBLEM: "Invalid JSON"
SOLUTION: 
- Check your JSON file for missing commas or brackets
- Use an online JSON validator to check syntax

PROBLEM: "Pages don't exist"
SOLUTION: 
- Check the total number of pages in your PDF
- Make sure your "from" and "to" page numbers are valid

===============================================================================
TIPS FOR SUCCESS
===============================================================================

1. Start Small: Try extracting just one chapter first
2. Check Page Numbers: Open your PDF and note the actual page numbers
3. Use Descriptive Names: Make your topic and chapter names clear
4. Test Your JSON: Start with just 2-3 chapters before processing hundreds
5. Backup Your Original: Always keep a copy of your original PDF
6. Use AI Tools: Let ChatGPT or Claude help create your JSON configuration

===============================================================================
GETTING HELP
===============================================================================

If you're stuck:
1. Check the file paths - are they correct?
2. Verify page numbers - do they exist in the PDF?
3. Test with a small example first
4. Check your JSON syntax using an online JSON validator

===============================================================================
EXAMPLE USE CASES
===============================================================================

- Medical Students: Split Harrison's Principles into disease-specific folders
- Law Students: Extract cases by topic from large casebooks  
- Researchers: Organize reference materials by subject
- Teachers: Create topic-specific reading materials
- Students: Break down large textbooks into manageable study chunks

===============================================================================
FILE ORGANIZATION TIPS
===============================================================================

BEFORE PROCESSING:
my_project/
├── pdf_cropper.py
├── extract_sections_v2.py
├── topics.json
└── large_textbook.pdf

AFTER PROCESSING:
my_project/
├── pdf_cropper.py
├── extract_sections_v2.py
├── topics.json
├── large_textbook.pdf
└── extracted_chapters/
    ├── 01_Topic_One/
    ├── 02_Topic_Two/
    └── 03_Topic_Three/

===============================================================================

Ready to get started? Follow the Quick Start Guide above and you'll be 
extracting PDF chapters in minutes!

Note: The topic-data2.json file was created using AI language models to 
automatically organize medical textbook chapters by clinical topics, making 
the process much faster than manual categorization.

=============================================================================== 