# BabySteps Digital School - Fixes and Verification Guide
**Date:** 2025-11-16  
**Issues Fixed:** Class 1 Science JSON Loading, MentorChat TTS, Ollama Connectivity

---

## 🔧 Issues Fixed

### 1. Class 1 Science JSON Not Loading ✅

**Problem:**
- LessonViewer was calling wrong API endpoint `/api/lessons/1`
- Actual curriculum API is `/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/`
- Curriculum files exist but weren't being fetched

**Fix Applied:**
- Updated `LessonViewer.js` `fetchLesson()` function to use correct URL pattern
- Added response wrapper handling for `{success: true, lesson: {...}}`
- Files: `frontend/src/components/LessonViewer.js` lines 211-230

**Verification Steps:**
```bash
# 1. Start Django backend
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000

# 2. In another terminal, start frontend
cd frontend
npm start

# 3. Open browser to http://localhost:3000
# 4. Click "Start Learning"
# 5. Click "Start Interactive Lesson" on dashboard
# 6. Verify lesson content loads (should see "Living and Non-Living Things" or similar)
```

**Expected Result:**
- Lesson loads with title, objectives, vocabulary, and content blocks
- TTS starts speaking the lesson content automatically
- No "Failed to load lesson" error

---

### 2. MentorChat TTS Not Working ✅

**Problem:**
- Backend returns response in `response.data.text` field
- Frontend was looking for `response.data.response` field
- Field name mismatch caused TTS to receive `undefined`

**Fix Applied:**
- Updated `MentorChat.js` to handle both field names: `text` OR `response`
- Added validation to ensure text exists before calling TTS
- Files: `frontend/src/components/MentorChat.js` lines 162-176

**Verification Steps:**
```bash
# Prerequisites: Backend and frontend running (see above)

# 1. Open http://localhost:3000
# 2. Click "Start Learning"
# 3. Look for floating chat panel (bottom-right, green border)
# 4. Click to open MentorChat
# 5. Type a question: "What is photosynthesis?"
# 6. Press Enter or click Send
# 7. Wait for response (5-10 seconds)
```

**Expected Result:**
- Bot response appears in chat
- TTS automatically speaks the response
- Voice should be Indian English female (if available)
- Speaking indicator shows "🔊 Speaking..."

---

### 3. MentorChat → Ollama Connectivity ✅

**Problem:**
- Need to verify end-to-end connectivity: React → Django → Ollama
- Ollama service must be running and model must be available
- Backend must be able to reach Ollama API

**Verification Steps:**

#### A. Automated Test (Recommended)
```bash
# Run the connectivity test script
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
python test_mentor_ollama.py
```

**Expected Output:**
```
=== Testing Direct Ollama Connection ===
✅ Ollama is running at http://127.0.0.1:11434
📦 Available models: ['llama3.2']
✅ Model 'llama3.2' is available

=== Testing Ollama Generation ===
✅ Ollama generated response:
   Hello from Ollama! I'm here to help you with any questions...

=== Testing Django Backend ===
✅ Django server is running at http://localhost:8000
✅ Django → Ollama connection working!
   Teacher: Aarini
   Response: Photosynthesis is the process by which plants make their own food...

SUMMARY
✅ PASS - Ollama Connection
✅ PASS - Ollama Generation
✅ PASS - Django → Ollama
🎉 All tests passed! MentorChat should work correctly.
```

#### B. Manual Test
```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/tags

# 2. Test Ollama generation
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Say hello",
  "stream": false
}'

# 3. Test Django endpoint
curl -X POST http://localhost:8000/api/mentor/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is water?",
    "class_number": 1,
    "subject": "science"
  }'
```

**Expected Result:**
- All three curl commands return valid JSON responses
- No connection errors or timeouts
- Django response includes `"success": true` and `"text": "..."`

---

## 🚀 Complete Startup Procedure

### Option 1: Using PowerShell Script
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\start_babysteps.ps1
```

### Option 2: Manual Startup

**Terminal 1 - Ollama:**
```bash
ollama serve
```

**Terminal 2 - Django Backend:**
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

**Terminal 3 - React Frontend:**
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend
npm start
```

---

## 🧪 End-to-End Test Checklist

### Class 1 Science Lesson
- [ ] Navigate to http://localhost:3000
- [ ] Click "Start Learning"
- [ ] Dashboard loads with student info and progress cards
- [ ] Click "Start Interactive Lesson"
- [ ] Lesson title appears: "Living and Non-Living Things" (or similar)
- [ ] TTS starts speaking automatically
- [ ] Can pause/resume/stop TTS
- [ ] Can navigate between content blocks
- [ ] Voice selector dropdown shows available voices

### MentorChat
- [ ] Floating chat panel visible (bottom-right)
- [ ] Click to open chat
- [ ] Teacher name shows: "Aarini" for Class 1 Science
- [ ] Type question: "What is a plant?"
- [ ] Response appears within 10 seconds
- [ ] TTS speaks the response automatically
- [ ] Can use microphone button for voice input
- [ ] Can toggle TTS play/pause
- [ ] Multiple messages work correctly

### Ollama Connectivity
- [ ] Run `python test_mentor_ollama.py` - all tests pass
- [ ] No 502 Bad Gateway errors in browser console
- [ ] No "Ollama request failed" errors in Django terminal
- [ ] Response time < 15 seconds for typical questions
- [ ] Responses are contextually appropriate for Class 1

---

## 🐛 Troubleshooting

### Issue: "Failed to load lesson"
**Solution:**
1. Check Django is running: `http://localhost:8000/api/`
2. Verify curriculum files exist: `curriculam/class1/EVS/Month1/Week_1/Lessons/`
3. Check Django terminal for errors
4. Try: `http://localhost:8000/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/`

### Issue: MentorChat TTS not speaking
**Solution:**
1. Open browser console (F12)
2. Check for "Speech synthesis error" messages
3. Verify voices loaded: Look for "Voices loaded: (327)" in console
4. Try different browser (Chrome/Edge recommended)
5. Check system audio is not muted

### Issue: "Ollama request failed"
**Solution:**
1. Run: `python test_mentor_ollama.py`
2. If Ollama not running: `ollama serve`
3. If model missing: `ollama pull llama3.2`
4. Check OLLAMA_BASE_URL: Should be `http://127.0.0.1:11434`
5. Restart Django after fixing Ollama

### Issue: 404 errors in browser console
**Solution:**
1. Check all three services are running (Ollama, Django, React)
2. Verify ports: Ollama (11434), Django (8000), React (3000)
3. Check for port conflicts: `netstat -ano | findstr "8000"`
4. Clear browser cache and reload

---

## 📊 Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Lesson Load | < 2 seconds | First load may be slower (cache) |
| MentorChat Response | 5-15 seconds | Depends on Ollama/question complexity |
| TTS Start | < 1 second | After response received |
| Voice Input | < 2 seconds | After speaking stops |

---

## 🔍 Monitoring

### Django Terminal
Watch for:
- `INFO: Lesson loaded successfully: EVS_C1_M1_W1_D1.json`
- `INFO: Lesson requested: Class 1, EVS, Month 1, Week 1, Day 1`
- No `ERROR` or `WARNING` messages

### Browser Console
Watch for:
- `✅ React content found in DOM`
- `Voices loaded: (327)` or similar
- `🎯 CURRENT VIEW: lesson`
- No red error messages

### Ollama Terminal
Watch for:
- `[GIN] POST /api/generate` requests
- Response times < 10s
- No connection errors

---

## 📝 Notes

1. **First Load:** May take longer due to cache warming
2. **Voice Selection:** Prefers Indian English female voices (Heera, Ravi, etc.)
3. **Auto-play:** TTS starts automatically for both lessons and chat responses
4. **Caching:** Lessons are cached for 1 hour to improve performance
5. **Ollama:** Must have `llama3.2` model pulled (`ollama pull llama3.2`)

---

## ✅ Success Criteria

All three issues are considered fixed when:

1. **Class 1 Science:** Lesson loads and displays content with TTS working
2. **MentorChat TTS:** Bot responses are spoken automatically
3. **Ollama:** `test_mentor_ollama.py` shows all tests passing

---

**Last Updated:** 2025-11-16  
**Tested On:** Windows 11, Chrome 120+, Python 3.11, Node 18+
