# 🎯 Master Case Integration Documentation

## Overview

The Master Case Integration connects the CBL (Case-Based Learning) assessment workflow with the 13-part master case document generation system. This integration allows users to go from curriculum documents to fully generated master case documents in a seamless workflow.

## 📁 File Structure

```
├── js/
│   └── master-case-integration.js     # Main integration logic
├── services/
│   ├── master_case_generator.py       # Backend master case generation
│   ├── reference_processor.py         # Reference document processing
│   └── case_management.py             # Workflow coordination
├── routers/
│   ├── assessment.py                  # Assessment API endpoints
│   └── tables.py                      # Document processing endpoints
├── case-creator.html                  # Main frontend interface
└── test-master-case-integration.html  # Testing interface
```

## 🔄 Complete Workflow

### 1. Document Upload & Processing
```
User uploads curriculum document → 
Docling processes to markdown → 
Reference context created → 
Topics extracted with competencies
```

### 2. Assessment Case Generation
```
User selects topic → 
AI generates case recommendations → 
User reviews and approves cases → 
Cases ready for master generation
```

### 3. Master Case Generation (NEW!)
```
Approved cases + Reference context → 
AI generates 13-part master cases → 
Markdown documents saved → 
Success/failure feedback
```

## 🚀 API Integration

### Frontend → Backend Flow

**Frontend (case-creator.html):**
```javascript
// When user clicks "Approve & Generate Master Cases"
approveAssessment() → 
  calls /api/assessment/generate-master-cases-from-assessment
```

**Backend API Chain:**
```python
assessment.py → case_management.py → master_case_generator.py
                     ↓
              reference_processor.py (gets context)
```

### Key API Endpoint

**POST** `/api/assessment/generate-master-cases-from-assessment`

**Request:**
```json
{
  "topic_id": "topic-0",
  "approved_cases": [
    {
      "caseTitle": "Acute Myocardial Infarction",
      "scenario": "A 55-year-old male presents...",
      "primaryCompetencies": ["GM5.10", "GM5.11"],
      "reasoning": "Tests diagnostic skills...",
      "setting": "Emergency Department"
    }
  ],
  "original_topic_data": { ... }
}
```

**Response:**
```json
{
  "success": true,
  "topic_id": "topic-0",
  "generated_cases": [
    {
      "case_title": "Acute Myocardial Infarction",
      "disease_name": "Acute_Myocardial_Infarction",
      "saved_path": "cache/case_docs/Acute_Myocardial_Infarction.md",
      "message": "Master case generated successfully"
    }
  ],
  "failed_cases": [],
  "total_cases": 1,
  "successful_generations": 1,
  "failed_generations": 0
}
```

## 🎨 Frontend Components

### 1. Loading Modal
- Shows progress during master case generation
- Displays case count and estimated time
- Animated indicators for different stages

### 2. Success Modal
- Lists all generated master cases
- Provides download and preview options
- Shows generation statistics
- Next steps guidance

### 3. Error Modal
- Detailed error messages
- Troubleshooting suggestions
- Option to retry or edit cases

## 📋 Testing

### Test File: `test-master-case-integration.html`

**Test Functions:**
- `testMasterCaseGeneration()` - Full API integration test
- `testLoadingModal()` - UI loading state test
- `testSuccessModal()` - Success display test
- `testErrorModal()` - Error handling test

**To run tests:**
1. Open `test-master-case-integration.html` in browser
2. Click test buttons to verify each component
3. Check console for detailed logs

## 🔧 Configuration

### Required Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Required Dependencies
```bash
pip install docling google-genai
```

### Directory Structure
```
cache/
├── topic-references/
│   └── topic-0/
│       ├── uploaded-file.pdf
│       └── topic-0_reference_context.md
└── case_docs/
    ├── Acute_Myocardial_Infarction.md
    └── Heart_Failure.md
```

## 🎯 Usage Instructions

### For End Users:

1. **Upload Reference Documents**
   - Upload curriculum PDFs/DOCX files
   - System processes with docling automatically
   - Reference context files created

2. **Generate Assessment Cases**
   - Select topic from uploaded documents
   - AI generates case recommendations
   - Review and customize cases as needed

3. **Generate Master Cases** (NEW!)
   - Click "Approve & Generate Master Cases"
   - System creates 13-part master case documents
   - Download or preview generated cases

### For Developers:

1. **Extend the Integration**
   ```javascript
   // Add new functionality to master-case-integration.js
   window.masterCaseIntegration.newFunction = function() {
       // Your code here
   };
   ```

2. **Customize UI Components**
   - Modify modal templates in `js/master-case-integration.js`
   - Update styling with Tailwind classes
   - Add new buttons/actions as needed

3. **Backend Extensions**
   - Add new endpoints in `routers/assessment.py`
   - Extend services in `services/` directory
   - Modify master case prompt in `master_case_generator.py`

## 🐛 Troubleshooting

### Common Issues:

1. **"Reference context not found"**
   - Ensure reference documents are uploaded first
   - Check that docling processing succeeded
   - Verify topic ID mapping

2. **"Gemini API error"**
   - Check GEMINI_API_KEY environment variable
   - Verify API quota and permissions
   - Check network connectivity

3. **"Master case generation failed"**
   - Review case titles and scenarios for formatting
   - Check server logs for detailed errors
   - Try with fewer cases if timeout occurs

### Debug Mode:
```javascript
// Enable debug logging
window.masterCaseState.debug = true;
```

## 🚀 Future Enhancements

1. **Preview Functionality**
   - Add endpoint to preview generated cases
   - Implement in-browser markdown rendering

2. **Batch Processing**
   - Queue multiple topic generations
   - Progress tracking for large batches

3. **Template Customization**
   - Allow users to modify the 13-part template
   - Save custom templates per institution

4. **Integration with LMS**
   - Export to SCORM packages
   - Direct integration with learning platforms

## 📞 Support

For issues or questions:
1. Check the test file for component verification
2. Review console logs for detailed error messages
3. Verify all dependencies are installed
4. Ensure environment variables are configured

---

**Last Updated:** December 2024  
**Version:** 1.0.0 