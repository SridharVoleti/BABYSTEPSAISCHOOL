# MentorChat Connection Diagnostic

## Current Status Check

### ✅ Confirmed Working:
1. **Ollama**: Running and responding to `ollama run llama3.2`
2. **Django Backend**: Test shows 200 OK with proper response
3. **Backend → Ollama**: Full chain working

### 🔍 Issue: Frontend MentorChat Not Connecting

## Step-by-Step Diagnosis

### 1. Check Browser Console

Open browser at `http://localhost:3000` and press **F12** to open DevTools.

**Look for these errors:**

#### A. CORS Error
```
Access to XMLHttpRequest at 'http://localhost:8000/api/mentor/chat' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:** Check Django CORS settings in `backend/settings.py`

#### B. 404 Not Found
```
POST http://localhost:8000/api/mentor/chat 404 (Not Found)
```

**Solution:** URL mismatch - check endpoint

#### C. Network Error
```
AxiosError: Network Error
```

**Solution:** Django backend not running

#### D. 500 Internal Server Error
```
POST http://localhost:8000/api/mentor/chat 500 (Internal Server Error)
```

**Solution:** Check Django terminal for Python errors

### 2. Check Network Tab

In DevTools, go to **Network** tab:

1. Clear all requests (🚫 icon)
2. Open MentorChat
3. Type a message and send
4. Look for `chat` request

**Check:**
- **Request URL**: Should be `http://localhost:8000/api/mentor/chat/`
- **Status**: Should be `200`
- **Response**: Should have `success: true` and `text` field

**If you see the request:**
- Click on it
- Go to **Response** tab
- Copy the response and share it

**If you DON'T see the request:**
- The frontend code might not be sending it
- Check Console for JavaScript errors

### 3. Verify Frontend Code Loaded

In browser Console, type:
```javascript
console.log('axiosInstance:', window.axiosInstance);
```

Or check if the updated code is loaded by looking at the MentorChat component source.

### 4. Check if Old Code is Cached

**Hard Refresh:**
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Or Clear Cache:**
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

## Quick Tests

### Test 1: Backend Direct (Already Passed ✅)
```powershell
python test_mentor_simple.py
```
**Result:** ✅ SUCCESS

### Test 2: Frontend API Call (Browser Console)

Open browser console and paste:
```javascript
fetch('http://localhost:8000/api/mentor/chat/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello',
    class_number: 1,
    subject: 'science'
  })
})
.then(r => r.json())
.then(d => console.log('Response:', d))
.catch(e => console.error('Error:', e));
```

**Expected:** Should log response with `success: true`

### Test 3: Check MentorChat Component

In browser console:
```javascript
// Check if MentorChat is rendered
document.querySelector('[class*="MentorChat"]') || 
document.querySelector('button:contains("Aarini")')
```

## Common Issues & Fixes

### Issue 1: MentorChat Button Not Visible
**Check:** Is the green chat button in bottom-right corner?
**Fix:** Scroll down or check if MentorChat component is rendered

### Issue 2: Button Visible But No Response
**Check:** Browser console for errors
**Likely:** Frontend code not updated or cached

### Issue 3: Response Received But Not Displayed
**Check:** Console for `response.data` structure
**Fix:** Frontend expecting wrong field name

### Issue 4: Response Displayed But TTS Not Working
**Check:** Browser supports Web Speech API
**Fix:** Use Chrome or Edge browser

## What to Share for Further Help

If still having issues, please share:

1. **Browser Console Errors** (screenshot or copy text)
2. **Network Tab** (screenshot of failed request)
3. **Django Terminal Output** (any errors when you send message)
4. **Which browser** you're using
5. **Exact steps** you're taking

## Expected Working Flow

1. Open `http://localhost:3000`
2. Select Class 1
3. Click "Start Learning"
4. See green chat button (bottom-right): "Aarini - Science"
5. Click button → Chat panel opens
6. Type "Hello" → Press Enter
7. See "Sending..." indicator
8. Wait 5-10 seconds
9. Response appears from Aarini
10. TTS speaks the response
11. Speaking indicator shows "🔊 Speaking..."

## Emergency Reset

If nothing works:

1. **Stop all servers** (Ctrl+C in all terminals)
2. **Close all browser tabs**
3. **Clear browser cache completely**
4. **Restart in order:**
   - Ollama (already running)
   - Django: `python manage.py runserver 8000`
   - Frontend: `npm start` (in frontend folder)
5. **Hard refresh browser** (Ctrl+Shift+R)
6. **Try again**

---

**Next Step:** Please check browser console and share any errors you see!
