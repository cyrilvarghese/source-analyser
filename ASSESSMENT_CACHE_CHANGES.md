# Assessment Cache Key Changes

## Overview
Changed the assessment caching system from timestamp-based keys to topic-name-based keys for better organization and retrieval.

## Changes Made

### 1. Backend Changes (`routers/tables.py`)

#### Modified `save_assessment_cache()` function:
- **Before**: Used `assessment_{timestamp}` format (e.g., "assessment_1749199812429")
- **After**: Uses sanitized topic name (e.g., "Liver_Disease", "Cardiac_Arrhythmias")

```python
# OLD CODE:
cache_id = cache_data['id']  # Used timestamp-based ID from frontend

# NEW CODE:
topic_name = cache_data.get('topic', 'Unknown_Topic')
sanitized_topic = sanitize_topic_name(topic_name)
cache_id = sanitized_topic if sanitized_topic else f"topic_{int(time.time())}"
```

#### Added cache replacement logic:
- When the same topic is cached again, it replaces the old cache file
- Prevents accumulation of multiple cache files for the same topic
- Maintains one assessment per topic approach

#### Enhanced cache mapping:
- Added `cache_id` field to store the topic-based key
- Maintains backward compatibility with existing cache structure

### 2. Frontend Changes (`case-creator.html`)

#### Modified `cacheAssessmentResult()` function:
- **Before**: Generated timestamp-based ID: `id: assessment_${Date.now()}`
- **After**: Uses topic name directly: `id: topicName`

```javascript
// OLD CODE:
const cacheData = {
    id: `assessment_${Date.now()}`,
    // ...
};

// NEW CODE:
const topicName = result.topic || originalTopic.topic;
const cacheData = {
    id: topicName,  // Use topic name as cache key
    // ...
};
```

## Benefits

### 1. **Better Organization**
- Cache files are named after topics (e.g., `Liver_Disease.json`)
- Easy to identify and manage cache files manually
- Logical grouping in cache directory

### 2. **Predictable Cache Keys**
- Same topic always maps to the same cache key
- No duplicate assessments for the same topic
- Consistent retrieval mechanism

### 3. **Cache Replacement**
- New assessments for the same topic replace old ones
- Prevents cache directory bloat
- Always contains the latest assessment for each topic

### 4. **Backward Compatibility**
- Existing cache endpoints work unchanged
- Frontend loading functions work with new key format
- Graceful fallback for edge cases

## Cache Key Format

### Topic Name Sanitization
The `sanitize_topic_name()` function processes topic names:
- Removes special characters except alphanumeric, spaces, and hyphens
- Replaces spaces and hyphens with underscores
- Examples:
  - "Liver Disease" → "Liver_Disease"
  - "Cardiac Arrhythmias & Conduction" → "Cardiac_Arrhythmias_Conduction"
  - "Type 2 Diabetes Management" → "Type_2_Diabetes_Management"

### Fallback Mechanism
If topic name sanitization fails, falls back to: `topic_{timestamp}`

## Directory Structure

```
cache/assessments/
├── assessment_cache_map.json     # Maps cache keys to file paths
├── Liver_Disease.json           # Assessment for Liver Disease topic
├── Cardiac_Arrhythmias.json     # Assessment for Cardiac Arrhythmias topic
└── Diabetes_Management.json     # Assessment for Diabetes Management topic
```

## Testing

Run the test script to verify the changes:
```bash
python test_topic_cache.py
```

The test demonstrates:
- Caching multiple topics with topic-based keys
- Cache replacement when same topic is cached again
- Proper sanitization of topic names
- Retrieval using sanitized topic names

## Migration

- **No action required** for existing cached assessments
- Old timestamp-based cache files will remain accessible
- New assessments will use topic-based keys
- System handles both formats seamlessly

## API Compatibility

All existing API endpoints remain unchanged:
- `POST /api/tables/assessment/cache-result/`
- `GET /api/tables/assessment/cached-results/`
- `GET /api/tables/assessment/cached-result/{cache_id}/`

The `cache_id` parameter now accepts both:
- Legacy timestamp format: `assessment_1749199812429`
- New topic format: `Liver_Disease` 