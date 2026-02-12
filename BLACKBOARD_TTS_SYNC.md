# Blackboard & TTS Synchronization

**Date**: December 11, 2025  
**Issue**: Text writing too fast compared to TTS voice

---

## ⚡ Changes Made

### Animation Speed
- **Before**: 80ms per character
- **After**: 250ms per character
- **Result**: Writing is now 3x slower

---

## 🎯 Synchronization Goals

### Perfect Sync Requires:
1. **Writing finishes** → Then **TTS speaks that word**
2. **TTS lags 0.1s** behind writing completion
3. Natural, teacher-like pace

### Current Configuration:
```javascript
// VirtualBlackboard.js
speed = 250ms per character

// TTS Settings (TTSService.js)
rate = 0.8 (slow and steady)
```

---

## 📊 Speed Calculations

### Writing Speed
- **250ms per character**
- Average word: 5 characters
- **Time per word**: 5 × 250ms = 1250ms (1.25 seconds)
- **Words per minute**: ~48 WPM

### TTS Speed
- **Rate 0.8** = 80% of normal speed
- Normal speech: ~150-160 WPM
- **TTS at 0.8**: ~120-130 WPM

**Current gap**: TTS still 2-3x faster than writing

---

## 🔧 Fine-Tuning Options

### Option 1: Adjust TTS Rate
Slow down TTS to match writing:
```javascript
// In TTSService.js
const utterance = new SpeechSynthesisUtterance(text);
utterance.rate = 0.5; // Even slower (was 0.8)
```

### Option 2: Speed Up Writing
Increase character speed:
```javascript
// In VirtualBlackboard.js
speed = 150 // Faster than 250ms
```

### Option 3: Variable Speed
Fast for punctuation, slow for letters:
```javascript
const charSpeed = (char) => {
  if (char === ' ') return 50;  // Fast for spaces
  if ('.!?'.includes(char)) return 300; // Pause at punctuation
  return 200; // Normal speed
};
```

---

## 🎬 Recommended Settings

### For Perfect Sync:
```javascript
// VirtualBlackboard.js
speed = 200 // ms per character

// TTSService.js  
rate = 0.6 // Slower speech
```

This gives:
- **Writing**: ~50 WPM
- **TTS**: ~90 WPM
- TTS finishes just after each word written

---

## 🧪 Testing

### Manual Test:
1. Write "Hello world" (11 chars)
2. At 250ms/char = 2750ms total
3. TTS at rate 0.8 should take ~3000ms
4. Result: TTS finishes 250ms after writing ✓

### Current Reality:
- Writing taking **too long**
- TTS finishing **before** writing done
- Need to either:
  - Speed up writing (reduce 250ms)
  - Or slow down TTS more (reduce 0.8)

---

## ✅ Quick Fix

If TTS is still too fast, adjust in two places:

### 1. Reduce Writing Speed
```javascript
// VirtualBlackboard.js line 24
speed = 180 // Instead of 250
```

### 2. Slow Down TTS
```javascript
// TTSService.js (search for "rate")
utterance.rate = 0.55; // Instead of 0.8
```

---

## 📈 Speed Comparison Table

| Speed (ms/char) | WPM (Writing) | TTS Rate | TTS WPM | Sync Quality |
|-----------------|---------------|----------|---------|--------------|
| 80 (old) | 150 | 0.8 | 120 | ❌ Writing too fast |
| 250 (current) | 48 | 0.8 | 120 | ❌ TTS too fast |
| 200 | 60 | 0.8 | 120 | ⚠️ TTS still faster |
| 200 | 60 | 0.6 | 90 | ✅ Better sync |
| 180 | 67 | 0.6 | 90 | ✅ Good sync |
| 150 | 80 | 0.55 | 85 | ✅ Best sync |

---

## 🎯 Ideal Configuration

```javascript
// VirtualBlackboard.js
const VirtualBlackboard = ({ content, onComplete, speed = 180 }) => {

// TTSService.js (find setupUtterance function)
utterance.rate = 0.6;
```

This achieves:
- Writing: ~67 WPM
- TTS: ~90 WPM  
- TTS lags ~0.3s behind each word
- Natural teacher pace

---

**Status**: Speed adjusted to 250ms (3x slower)  
**Next**: Fine-tune to 180ms if still needed  
**Test**: Refresh browser and compare writing vs TTS
