# TTS Troubleshooting Guide

**Date**: 2025-11-26  
**Issue**: TTS not working in browser

---

## Quick Diagnosis Steps

### Step 1: Test Browser TTS Support

Open this test file in your browser:
```
file:///d:/Sridhar/Projects/BabyStepsDigitalSchool/test_tts_browser.html
```

**What to check:**
1. ✅ Does it say "Speech Synthesis IS supported"?
2. ✅ Do you see voices listed?
3. ✅ Does the "Test Basic Speech" button work?
4. ✅ Does the "Test Indian English" button work?

**If NO to any**: Your browser doesn't support TTS or voices aren't loaded.

---

### Step 2: Check Browser Console

1. Open your React app: http://localhost:3000
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Look for these messages:

**Expected (Good):**
```
TTS Service initialization started - waiting for voices...
TTS: Checking voices, found: X
TTS: Service is ready with X voices
```

**Problematic (Bad):**
```
TTS: Speech synthesis not supported
TTS: No voices loaded
Error: [any TTS-related error]
```

---

### Step 3: Check React App State

In the browser console, type:
```javascript
// Check if TTS service exists
window.speechSynthesis

// Check voices
speechSynthesis.getVoices()

// Test speech directly
const u = new SpeechSynthesisUtterance('Hello');
speechSynthesis.speak(u);
```

---

## Common Issues & Solutions

### Issue 1: "Speech Synthesis not supported"

**Cause**: Browser doesn't support Web Speech API

**Solution**:
- ✅ Use Chrome, Edge, or Firefox (recommended)
- ❌ Don't use Internet Explorer
- ⚠️ Safari works but may have limitations

---

### Issue 2: "No voices found" or voices.length = 0

**Cause**: Voices not loaded yet

**Solution**:
1. **Wait a moment** - voices load asynchronously
2. **Click anywhere** on the page - browser needs user interaction
3. **Reload the page** - sometimes helps
4. **Check system voices**:
   - Windows: Settings → Time & Language → Speech
   - macOS: System Preferences → Accessibility → Speech

---

### Issue 3: TTS buttons visible but no sound

**Cause**: Multiple possible reasons

**Solutions**:

1. **Check system volume**:
   - Unmute system
   - Check browser isn't muted (right-click browser tab)
   - Test with YouTube to verify sound works

2. **User interaction required**:
   - Click anywhere on the page first
   - Browser autoplay policies require user gesture

3. **Check browser console for errors**:
   - Press F12
   - Look for red error messages
   - Share errors for help

4. **Try different browser**:
   - Chrome (best support)
   - Edge (best on Windows)
   - Firefox (good support)

---

### Issue 4: TTS works in test file but not in React app

**Cause**: React app initialization issue

**Solution**:

1. **Check if TTSProvider is wrapping App**:
   ```javascript
   // In App.tsx, should see:
   <TTSProvider>
     <App />
   </TTSProvider>
   ```

2. **Check if TTSService is imported**:
   ```javascript
   // In components using TTS:
   import { useLessonTTS } from '../contexts/TTSContext';
   ```

3. **Hard refresh browser**:
   - Windows: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

4. **Clear browser cache**:
   - Chrome: Settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Click "Clear data"

---

### Issue 5: "Voices loaded: 0" in console

**Cause**: System voices not installed or not accessible

**Solution**:

**Windows:**
```powershell
# Check installed voices
Get-WmiObject Win32_SpeechVoice | Select-Object Name, Language
```

**Install Indian English voices:**
1. Settings → Time & Language → Speech
2. Click "Add voices"
3. Search for "English (India)"
4. Install "Microsoft Ravi" or "Microsoft Heera"

**macOS:**
1. System Preferences → Accessibility → Speech
2. System Voice → Customize
3. Check "Ravi" or "Veena" (Indian English)
4. Download if needed

**Linux:**
```bash
# Install espeak-ng
sudo apt-get install espeak-ng

# Test
espeak-ng "Hello, this is a test"
```

---

## Step-by-Step Debugging

### Debug Step 1: Test in Isolation

1. Open `test_tts_browser.html` in browser
2. Click "Test Basic Speech"
3. **If this works**: Browser TTS is fine, issue is in React app
4. **If this doesn't work**: Browser TTS issue, see solutions above

---

### Debug Step 2: Check React Console

1. Open React app: http://localhost:3000
2. Press F12 → Console
3. Type: `speechSynthesis.getVoices()`
4. **If returns array with voices**: TTS should work
5. **If returns empty array**: Wait 2 seconds and try again

---

### Debug Step 3: Force TTS Test in React

In browser console:
```javascript
// Test TTS directly
const test = new SpeechSynthesisUtterance('Testing one two three');
test.rate = 0.8;
test.onstart = () => console.log('Started!');
test.onend = () => console.log('Ended!');
test.onerror = (e) => console.error('Error:', e);
speechSynthesis.speak(test);
```

**If this works**: React TTS service should work too.

---

### Debug Step 4: Check Component State

In React DevTools (F12 → Components tab):
1. Find `TTSProvider` component
2. Check state:
   - `isReady`: should be `true`
   - `voices`: should have array of voices
   - `isSpeaking`: changes when speaking

---

## Quick Fixes

### Fix 1: Force Voice Reload

In browser console:
```javascript
// Force reload voices
speechSynthesis.cancel();
const voices = speechSynthesis.getVoices();
console.log('Voices:', voices.length);

// If 0, wait and try again
setTimeout(() => {
  const v = speechSynthesis.getVoices();
  console.log('Voices after delay:', v.length);
}, 1000);
```

---

### Fix 2: Restart Everything

```powershell
# Stop all services (Ctrl+C in each terminal)

# Clear browser cache
# Chrome: Ctrl+Shift+Delete → Clear cache

# Restart services
# Terminal 1:
ollama serve

# Terminal 2:
cd D:\Sridhar\Projects\BabyStepsDigitalSchool
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000

# Terminal 3:
cd D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend
npm start

# Open browser in incognito mode
# Chrome: Ctrl+Shift+N
# Navigate to: http://localhost:3000
```

---

### Fix 3: Enable Autoplay in Browser

**Chrome:**
1. Go to: chrome://settings/content/sound
2. Ensure "Sites can play sound" is enabled
3. Add http://localhost:3000 to allowed list

**Edge:**
1. Go to: edge://settings/content/mediaAutoplay
2. Set to "Allow"

---

## Verification Checklist

After applying fixes, verify:

- [ ] `test_tts_browser.html` works
- [ ] Browser console shows "TTS: Service is ready"
- [ ] `speechSynthesis.getVoices()` returns voices
- [ ] Clicking anywhere on page enables audio
- [ ] LessonViewer shows TTS controls
- [ ] Clicking "Replay" button speaks
- [ ] MentorChat responses speak automatically
- [ ] No errors in console

---

## Still Not Working?

### Collect Diagnostic Information:

1. **Browser info**:
   ```javascript
   console.log('Browser:', navigator.userAgent);
   console.log('TTS supported:', !!window.speechSynthesis);
   console.log('Voices:', speechSynthesis.getVoices().length);
   ```

2. **React app state**:
   - Open React DevTools
   - Check TTSProvider state
   - Screenshot any errors

3. **Console logs**:
   - Copy all console messages
   - Include any red errors
   - Include TTS-related logs

4. **System info**:
   - Operating System
   - Browser version
   - Installed voices

---

## Contact Support

If still not working, provide:
1. Browser and OS version
2. Output from `test_tts_browser.html`
3. Console logs from React app
4. Screenshot of issue
5. Steps you've tried

---

**Last Updated**: 2025-11-26  
**Status**: Troubleshooting Guide
