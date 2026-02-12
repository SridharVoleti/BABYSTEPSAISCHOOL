# BabySteps Digital School - Offline Setup Guide

## 🎯 **Fully Offline Application**

This application has been configured to work completely offline with all dependencies downloaded locally.

### **📦 What's Included for Offline Use:**

#### **Frontend Assets:**
- ✅ **React Application**: Complete with all dependencies (~50MB)
- ✅ **3D Avatar Libraries**:
  - Three.js (CDN): `https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.min.js`
  - TalkingHead (Local): `frontend/public/js/talkinghead-bundle.js` (213KB)
  - Lip Sync Modules (Local): `lipsync-en.mjs`, `dynamicbones.mjs`, etc.
- ✅ **Custom Avatar**: `ModelTeacher.glb` (958KB) - Your custom teacher avatar
- ✅ **Lesson Content**: All JSON lesson files
- ✅ **Audio Assets**: Background audio and sound effects

#### **Backend Assets:**
- ✅ **Django Framework**: Complete web framework
- ✅ **AI/ML Libraries**: Whisper, Transformers, PyTorch for offline processing
- ✅ **Audio Processing**: Librosa, PyDub, SoundFile
- ✅ **Database**: PostgreSQL with local data

### **🚀 Offline Usage:**

1. **Install Dependencies** (one-time setup):
   ```bash
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   ```

2. **Start Application** (works offline):
   ```bash
   # Terminal 1 - Backend
   cd backend
   python manage.py runserver 0.0.0.0:8000

   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

3. **Access Application**: `http://localhost:3000`

### **💾 Storage Requirements:**
- **Initial Download**: ~500MB (one-time)
- **Runtime**: ~200MB RAM
- **Storage**: ~100MB for application + lesson content

### **🔧 Technical Details:**

#### **Avatar System:**
- **Library**: TalkingHead 3D avatar with lip-sync
- **Model**: Custom `ModelTeacher.glb` (female teacher avatar)
- **Features**: Real-time lip-sync, mood expressions, TTS integration
- **Fallback**: Emoji avatar (🦉) if 3D loading fails

#### **Implementation Standards:**
- ✅ **Working GitHub Pages Implementation**: Copied exact approach from functional index.html
- ✅ **Import Maps**: ES6 module loading with import maps as used in working version
- ✅ **Local Modules**: Using local copies of talkinghead.mjs and dependencies
- ✅ **Named Imports**: Using `{ TalkingHead }` import syntax
- ✅ **speakAudio Method**: Primary method for lip-sync with audio callback
- ✅ **Simplified Constructor**: Minimal configuration matching working setup
- ✅ **Error Boundaries**: React error boundaries for crash prevention
- ✅ **DOM Cleanup**: Proper cleanup to prevent React DOM conflicts

#### **Network Independence:**
- ✅ **Minimal External APIs**: Only Three.js from CDN (cached locally)
- ✅ **Local TalkingHead**: Avatar library from local files
- ✅ **Self-contained**: Avatar system works offline
- ✅ **Local Assets**: All media files included
- ✅ **Database**: Local SQLite/PostgreSQL

### **🎮 Features Available Offline:**

1. **Interactive Lessons** with 3D avatar teacher
2. **Text-to-speech** with lip-sync animation
3. **Activity Games** (drag-drop, matching, etc.)
4. **Progress Tracking** and completion certificates
5. **Audio Recording** and playback
6. **Full Lesson Navigation** and adventure map

### **🔄 Update Process:**

When you want to update the application:

1. **Pull Latest Code**: `git pull`
2. **Update Dependencies**: `npm install && pip install -r requirements.txt`
3. **Download New Assets**: Scripts will automatically download new avatar libraries if needed
4. **Restart Services**: Application works immediately

---

**Status**: ✅ **100% OFFLINE READY**
**Last Updated**: 2025-10-17
**Avatar**: Custom ModelTeacher.glb (958KB)
