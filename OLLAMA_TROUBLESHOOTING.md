# Ollama Connection Troubleshooting Guide

**Date:** 2025-11-16  
**Status:** ✅ Backend Working | Frontend Needs Testing

---

## ✅ Current Status

### What's Working:
1. **Ollama Service**: Running at `http://127.0.0.1:11434` ✅
2. **Ollama Model**: `llama3.2:latest` available ✅
3. **Ollama Generation**: Responding correctly ✅
4. **Django Backend**: API endpoint working ✅
5. **Django → Ollama**: Full chain working ✅

### Test Results:
```bash
python test_mentor_simple.py
```
**Output:**
```json
{
  "success": true,
  "text": "Water is a special liquid that's essential for our bodies...",
  "teacher": "Aarini",
  "class": 1,
  "subject": "Science",
  "tts": {
    "enabled": true,
    "rate": 0.7,
    "pitch": 1.0,
    "voice": "female",
    "language": "en-IN"
  }
}
```

---

## 🔍 If MentorChat Still Not Working in Browser

### Step 1: Verify All Services Running

**Check Ollama:**
```powershell
# Should return list of models
curl http://localhost:11434/api/tags
```

**Check Django:**
```powershell
# Should return 200 OK
curl http://localhost:8000/api/
```

**Check Frontend:**
```
Open http://localhost:3000 in browser
```

### Step 2: Test Backend Directly

```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
python test_mentor_simple.py
```

**Expected:** ✅ SUCCESS with teacher response

### Step 3: Check Browser Console

1. Open browser DevTools (F12)
2. Go to Console tab
3. Click MentorChat button
4. Type a message and send
5. Look for errors

**Common Errors:**

#### Error: "Network Error" or "ERR_CONNECTION_REFUSED"
**Solution:** Django backend not running
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

#### Error: 404 Not Found
**Solution:** Wrong API endpoint
- Check: `/api/mentor/chat/` (with trailing slash)
- Frontend should use: `axiosInstance.post('mentor/chat', ...)`

#### Error: 500 Internal Server Error
**Solution:** Check Django terminal for Python errors
- Look for import errors
- Look for missing environment variables

#### Error: 502 Bad Gateway
**Solution:** Ollama not running
```powershell
ollama serve
```

### Step 4: Check Network Tab

1. Open DevTools → Network tab
2. Send a message in MentorChat
3. Look for `chat` request
4. Check:
   - **Request URL**: Should be `http://localhost:8000/api/mentor/chat/`
   - **Request Method**: POST
   - **Status**: 200
   - **Response**: Should have `success: true` and `text` field

### Step 5: Verify Frontend Code

**Check MentorChat.js:**
```javascript
// Should be using axiosInstance, not axios
import axiosInstance from '../api/axiosConfig';

// Endpoint should be relative (no leading slash)
const response = await axiosInstance.post('mentor/chat', {
  message,
  class_number: classNumber,
  subject
});

// Should handle 'text' field from backend
const responseText = response.data.text || response.data.response || '';
```

---

## 🚀 Complete Startup Procedure

### Terminal 1 - Ollama
```powershell
ollama serve
```
**Wait for:** `Ollama is running`

### Terminal 2 - Django Backend
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```
**Wait for:** `Starting development server at http://127.0.0.1:8000/`

### Terminal 3 - React Frontend
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend
npm start
```
**Wait for:** `Compiled successfully!` and browser opens

### Terminal 4 - Test (Optional)
```powershell
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
python test_mentor_simple.py
```
**Expected:** ✅ SUCCESS

---

## 🧪 Testing MentorChat in Browser

1. **Open** `http://localhost:3000`
2. **Select** Class 1
3. **Click** "Start Learning"
4. **Look** for floating chat button (bottom-right, green border)
5. **Click** chat button to open
6. **Type** "What is water?" and press Enter
7. **Wait** 5-10 seconds for response
8. **Verify:**
   - Response appears in chat
   - TTS speaks the response
   - Teacher name shows "Aarini"
   - No errors in console

---

## 📊 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Ollama startup | 5-10s | First time only |
| Django startup | 2-3s | |
| Frontend startup | 10-20s | |
| First chat response | 10-15s | Model loading |
| Subsequent responses | 3-8s | Faster after warmup |

---

## 🐛 Common Issues & Solutions

### Issue: "Ollama is not running"
**Check:**
```powershell
Get-Process ollama
```
**Fix:**
```powershell
ollama serve
```

### Issue: "Model not found"
**Check:**
```powershell
ollama list
```
**Fix:**
```powershell
ollama pull llama3.2
```

### Issue: "Port 8000 already in use"
**Find process:**
```powershell
netstat -ano | findstr :8000
```
**Kill process:**
```powershell
taskkill /PID <PID> /F
```

### Issue: "CORS error"
**Check Django settings:**
- `CORS_ALLOW_ALL_ORIGINS = True` (development only)
- `CORS_ALLOWED_ORIGINS` includes `http://localhost:3000`

### Issue: "TTS not speaking"
**Check:**
1. Browser supports Web Speech API (Chrome/Edge recommended)
2. System audio not muted
3. Response has `text` field (not empty)
4. Console shows "Voices loaded"

---

## 📝 Environment Variables

Create `.env` file in project root:
```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
DEBUG=True
```

---

## ✅ Success Checklist

- [ ] Ollama service running (`ollama serve`)
- [ ] Model available (`ollama list` shows llama3.2)
- [ ] Django backend running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] `test_mentor_simple.py` passes
- [ ] Browser console shows no errors
- [ ] MentorChat button visible
- [ ] Can send messages
- [ ] Receives responses
- [ ] TTS speaks responses

---

## 🆘 Still Having Issues?

1. **Restart everything:**
   - Stop all terminals (Ctrl+C)
   - Close all browser tabs
   - Start services in order: Ollama → Django → Frontend

2. **Check logs:**
   - Django terminal for Python errors
   - Browser console for JavaScript errors
   - Ollama terminal for model errors

3. **Run full diagnostic:**
   ```powershell
   python test_mentor_ollama.py
   ```

4. **Hard refresh browser:**
   - `Ctrl + Shift + R` (Windows/Linux)
   - `Cmd + Shift + R` (Mac)

---

**Last Updated:** 2025-11-16  
**Backend Status:** ✅ Working  
**Frontend Status:** Needs browser testing
