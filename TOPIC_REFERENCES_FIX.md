# Topic References Fix

## Problem
The topic references system was using index-based keys like "topic-0", "topic-1" instead of actual topic names like "liver_disease", "cardiac_arrhythmias".

## Root Cause
1. **Frontend Issue**: The `topicId` was generated as `topic-${topicIndex}` instead of using the actual topic name
2. **API Mismatch**: Frontend was sending topicId in URL path, but backend expected topic_name in form data

## Changes Made

### 1. Backend Changes (`routers/tables.py`)

#### Updated API Endpoint
```python
# OLD:
@router.post("/topics/references/")
async def attach_reference_to_topic(
    files: list[UploadFile] = File(...),
    topic_name: str = Form(""),
    description: str = Form("")
):

# NEW:
@router.post("/topics/{topic_name}/references/")
async def attach_reference_to_topic(
    topic_name: str,
    files: list[UploadFile] = File(...),
    description: str = Form("")
):
```

**Benefits:**
- Topic name now comes from URL path parameter
- Consistent with other endpoints like `GET /topics/{topic_name}/references/`
- No need for form data topic_name parameter

### 2. Frontend Changes (`case-creator.html`)

#### Updated Topic ID Generation
```javascript
// OLD:
const topicId = `topic-${topicIndex}`;

// NEW:
const topicId = sanitizeTopicName(topic.topic);
```

#### Added Topic Name Sanitization Function
```javascript
function sanitizeTopicName(topicName) {
    if (!topicName) return 'unknown_topic';
    // Replace spaces and special characters with underscores
    let sanitized = topicName.replace(/[^\w\s-]/g, '');
    sanitized = sanitized.replace(/[-\s]+/g, '_');
    return sanitized.trim('_').toLowerCase();
}
```

#### Updated API Calls
```javascript
// Upload references
xhr.open('POST', `/api/tables/topics/${encodeURIComponent(topicName)}/references/`);

// Download references  
fetch(`/api/tables/topics/${encodeURIComponent(topicName)}/references/${referenceId}/download/`)

// Delete references
fetch(`/api/tables/topics/${encodeURIComponent(topicName)}/references/${referenceId}/`, {method: 'DELETE'})

// List references
fetch(`/api/tables/topics/${encodeURIComponent(topicName)}/references/`)
```

#### Updated Function Signatures
```javascript
// OLD:
async function loadTopicReferences(topicId)
async function uploadReference(topicId)
async function downloadReference(topicId, referenceId)
async function deleteReference(topicId, referenceId, filename)

// NEW:
async function loadTopicReferences(topicId, topicName)
async function uploadReference(topicId, topicName)
async function downloadReference(topicName, referenceId)
async function deleteReference(topicName, referenceId, filename)
```

## Cache Key Format

### Topic Name Sanitization Examples
- "Liver Disease" → "liver_disease"
- "Cardiac Arrhythmias & Conduction" → "cardiac_arrhythmias_conduction"
- "Type 2 Diabetes Management" → "type_2_diabetes_management"

### Directory Structure
```
cache/topic-references/
├── references_map.json
├── liver_disease/
│   ├── 1749201545_Acute_Hepatitis.pdf
│   └── liver_disease_reference_context.md
├── cardiac_arrhythmias/
│   ├── 1749201600_ECG_Guide.pdf
│   └── cardiac_arrhythmias_reference_context.md
└── diabetes_management/
    ├── 1749201700_Diabetes_Guidelines.pdf
    └── diabetes_management_reference_context.md
```

### References Map Format
```json
{
  "Liver Disease": [
    {
      "id": "Liver Disease_1749201545_0",
      "filename": "Acute Hepatitis.pdf",
      "topic_name": "Liver Disease",
      "cache_key": "liver_disease",
      "file_path": "cache/topic-references/liver_disease/1749201545_Acute Hepatitis.pdf"
    }
  ]
}
```

## Migration

### For Existing Data
- Old "topic-0" entries will remain in references_map.json
- New uploads will use proper topic names
- System handles both formats during transition

### For New Installations
- All references will use topic-based keys from the start
- No migration needed

## Testing

Run the test script to verify the fix:
```bash
python test_topic_references_fix.py
```

The test will:
- Show current references map structure
- Identify old vs new format usage
- Test topic name sanitization
- Display directory structure
- Provide migration recommendations

## Benefits

1. **Better Organization**: Files organized by actual topic names
2. **Predictable Structure**: Easy to find references for specific topics
3. **Consistent Naming**: Matches assessment and master case caching patterns
4. **API Consistency**: All topic endpoints use the same URL pattern
5. **Developer Friendly**: Clear relationship between topic names and file storage

## API Compatibility

All endpoints now follow consistent pattern:
- `POST /api/tables/topics/{topic_name}/references/` - Upload references
- `GET /api/tables/topics/{topic_name}/references/` - List references  
- `GET /api/tables/topics/{topic_name}/references/{reference_id}/download/` - Download reference
- `DELETE /api/tables/topics/{topic_name}/references/{reference_id}/` - Delete reference

The `{topic_name}` parameter accepts the actual topic name (e.g., "Liver Disease") and the system handles URL encoding automatically. 