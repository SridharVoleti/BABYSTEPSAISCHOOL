# BabySteps Digital School - Complete Startup Guide

**Date**: 2025-11-26  
**Author**: BabySteps Development Team  
**Status**: ✅ Production Ready

---

## Quick Start (5 Minutes)

### Prerequisites Check
```powershell
# Check Python version (3.8+)
python --version

# Check Node.js version (14+)
node --version

# Check if Ollama is installed
ollama --version
```

### One-Command Startup
```powershell
# Run the automated startup script
.\start_babysteps.ps1
```

This will:
1. ✅ Start Ollama service
2. ✅ Activate Python virtual environment
3. ✅ Start Django backend (port 8000)
4. ✅ Start React frontend (port 3000)
5. ✅ Run health checks

---

## Detailed Setup Instructions

### Step 1: Install Prerequisites

#### 1.1 Python (3.8 or higher)
```powershell
# Download from python.org
# Verify installation
python --version
pip --version
```

#### 1.2 Node.js (14 or higher)
```powershell
# Download from nodejs.org
# Verify installation
node --version
npm --version
```

#### 1.3 Ollama (LLM Service)
```powershell
# Download from ollama.ai
# Install and verify
ollama --version

# Pull the required model
ollama pull llama3.2
```

---

### Step 2: Project Setup

#### 2.1 Clone Repository
```powershell
cd D:\Sridhar\Projects
git clone <repository-url> BabyStepsDigitalSchool
cd BabyStepsDigitalSchool
```

#### 2.2 Backend Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

#### 2.3 Frontend Setup
```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Return to root
cd ..
```

---

### Step 3: Start Services

#### 3.1 Start Ollama (Terminal 1)
```powershell
# Start Ollama service
ollama serve

# Keep this terminal open
# You should see: "Ollama is running"
```

#### 3.2 Start Django Backend (Terminal 2)
```powershell
# Navigate to project root
cd D:\Sridhar\Projects\BabyStepsDigitalSchool

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start Django server
python manage.py runserver 8000

# Keep this terminal open
# You should see: "Starting development server at http://127.0.0.1:8000/"
```

#### 3.3 Start React Frontend (Terminal 3)
```powershell
# Navigate to frontend
cd D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend

# Start React dev server
npm start

# Keep this terminal open
# Browser should open automatically to http://localhost:3000
```

---

### Step 4: Verify Installation

#### 4.1 Run Health Checks
```powershell
# In a new terminal (Terminal 4)
cd D:\Sridhar\Projects\BabyStepsDigitalSchool

# Test Ollama connectivity
python test_ollama_reliability.py

# Expected output:
# 🎉 ALL TESTS PASSED!
```

#### 4.2 Test Frontend
1. Open browser: http://localhost:3000
2. Select Class 1
3. Click "Start Learning"
4. Verify:
   - ✅ Lesson loads
   - ✅ TTS speaks automatically
   - ✅ Navigation works
   - ✅ MentorChat button visible

#### 4.3 Test MentorChat
1. Click the MentorChat button (bottom-right)
2. Type: "What is water?"
3. Press Enter or click Send
4. Verify:
   - ✅ Response appears (5-10 seconds)
   - ✅ TTS speaks the response
   - ✅ No connection errors
   - ✅ Teacher name shows "Aarini"

---

## Environment Configuration

### Backend Environment Variables

Create `.env` file in project root:

```env
# 2025-11-26: BabySteps Configuration

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Ollama Configuration
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_MAX_RETRIES=3
OLLAMA_TIMEOUT=60
OLLAMA_POOL_CONNECTIONS=10
OLLAMA_POOL_MAXSIZE=20

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
LOG_LEVEL=INFO
```

### Frontend Environment Variables

Create `.env` file in `frontend/` directory:

```env
# 2025-11-26: Frontend Configuration

# API Configuration
REACT_APP_API_URL=http://127.0.0.1:8000/api

# Feature Flags
REACT_APP_ENABLE_TTS=true
REACT_APP_ENABLE_MENTOR_CHAT=true

# Development
REACT_APP_ENV=development
```

---

## Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Ollama | 11434 | http://127.0.0.1:11434 |
| Django Backend | 8000 | http://127.0.0.1:8000 |
| React Frontend | 3000 | http://localhost:3000 |

**Important**: Ensure these ports are not in use by other applications.

---

## Troubleshooting

### Issue: Port Already in Use

**Symptoms:**
```
Error: Port 8000 is already in use
```

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F

# Or use different port
python manage.py runserver 8001
```

---

### Issue: Ollama Not Starting

**Symptoms:**
```
Cannot connect to Ollama at http://127.0.0.1:11434
```

**Solutions:**

1. **Check if Ollama is installed:**
   ```powershell
   ollama --version
   ```

2. **Start Ollama manually:**
   ```powershell
   ollama serve
   ```

3. **Check if model is available:**
   ```powershell
   ollama list
   # Should show llama3.2
   
   # If not, pull it:
   ollama pull llama3.2
   ```

4. **Check firewall:**
   - Allow Ollama through Windows Firewall
   - Port 11434 should be accessible

---

### Issue: Virtual Environment Not Activating

**Symptoms:**
```
.\venv\Scripts\Activate.ps1 : cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try activating again
.\venv\Scripts\Activate.ps1
```

---

### Issue: Frontend Not Starting

**Symptoms:**
```
npm ERR! Missing script: "start"
```

**Solutions:**

1. **Reinstall dependencies:**
   ```powershell
   cd frontend
   rm -rf node_modules
   rm package-lock.json
   npm install
   ```

2. **Check Node version:**
   ```powershell
   node --version
   # Should be 14 or higher
   ```

3. **Clear npm cache:**
   ```powershell
   npm cache clean --force
   npm install
   ```

---

### Issue: Database Errors

**Symptoms:**
```
django.db.utils.OperationalError: no such table
```

**Solution:**
```powershell
# Run migrations
python manage.py migrate

# If issues persist, reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

### Issue: CORS Errors

**Symptoms:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**

1. **Check Django settings:**
   ```python
   # backend/settings.py
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
   ]
   ```

2. **Restart Django server:**
   ```powershell
   # Stop server (Ctrl+C)
   # Start again
   python manage.py runserver 8000
   ```

---

### Issue: TTS Not Working

**Symptoms:**
- No sound when lesson loads
- TTS controls appear but don't work

**Solutions:**

1. **Check browser support:**
   - Use Chrome, Edge, or Firefox
   - Safari also supported

2. **User interaction required:**
   - Click anywhere on the page first
   - Browser autoplay policies

3. **Check system volume:**
   - Unmute system
   - Check browser isn't muted

4. **Check console for errors:**
   - Press F12
   - Look for TTS-related errors

---

## Performance Optimization

### Development Mode

**Recommended Settings:**
```env
# Faster startup, more logging
DEBUG=True
OLLAMA_TIMEOUT=60
OLLAMA_MAX_RETRIES=3
LOG_LEVEL=DEBUG
```

### Production Mode

**Recommended Settings:**
```env
# Optimized for performance
DEBUG=False
OLLAMA_TIMEOUT=30
OLLAMA_MAX_RETRIES=5
OLLAMA_POOL_CONNECTIONS=20
OLLAMA_POOL_MAXSIZE=50
LOG_LEVEL=WARNING
```

---

## Monitoring & Logs

### View Django Logs
```powershell
# Django logs appear in the terminal where you ran:
python manage.py runserver 8000

# For file logging, check:
tail -f logs/django.log
```

### View Ollama Logs
```powershell
# Ollama logs appear in the terminal where you ran:
ollama serve

# Or check system logs
```

### View Frontend Logs
```powershell
# React logs appear in the terminal where you ran:
npm start

# Browser console (F12) for runtime logs
```

### Health Check Endpoints

```powershell
# Check Ollama
curl http://localhost:11434/api/tags

# Check Django
curl http://localhost:8000/api/

# Check Mentor Chat Service
curl http://localhost:8000/api/mentor/health/
```

---

## Development Workflow

### Daily Startup Routine

1. **Start Ollama** (Terminal 1)
   ```powershell
   ollama serve
   ```

2. **Start Backend** (Terminal 2)
   ```powershell
   cd D:\Sridhar\Projects\BabyStepsDigitalSchool
   .\venv\Scripts\Activate.ps1
   python manage.py runserver 8000
   ```

3. **Start Frontend** (Terminal 3)
   ```powershell
   cd D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend
   npm start
   ```

4. **Open Browser**
   - http://localhost:3000

### Making Changes

**Backend Changes:**
1. Edit Python files
2. Django auto-reloads (no restart needed)
3. If models changed: `python manage.py makemigrations && python manage.py migrate`

**Frontend Changes:**
1. Edit React files
2. React auto-reloads (no restart needed)
3. If dependencies changed: `npm install`

**Ollama Changes:**
1. Stop Ollama (Ctrl+C)
2. Update model: `ollama pull llama3.2`
3. Restart: `ollama serve`

---

## Testing

### Run All Tests

```powershell
# Backend tests
python manage.py test

# Ollama reliability tests
python test_ollama_reliability.py

# Frontend tests
cd frontend
npm test
```

### Test Specific Components

```powershell
# Test mentor chat
python test_mentor_simple.py

# Test curriculum loader
python manage.py test services.curriculum_loader_service

# Test TTS (manual)
# Open browser, check console for TTS logs
```

---

## Backup & Recovery

### Backup Database

```powershell
# SQLite backup
copy db.sqlite3 db.sqlite3.backup

# With timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
copy db.sqlite3 "db.sqlite3.$timestamp.backup"
```

### Restore Database

```powershell
# Restore from backup
copy db.sqlite3.backup db.sqlite3

# Run migrations to ensure schema is current
python manage.py migrate
```

### Backup Configuration

```powershell
# Backup .env files
copy .env .env.backup
copy frontend\.env frontend\.env.backup
```

---

## Updating the Application

### Update Backend

```powershell
# Pull latest code
git pull

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Restart server
# Ctrl+C, then:
python manage.py runserver 8000
```

### Update Frontend

```powershell
# Pull latest code
git pull

# Update dependencies
cd frontend
npm install

# Restart server
# Ctrl+C, then:
npm start
```

### Update Ollama Model

```powershell
# Pull latest model
ollama pull llama3.2

# Restart Ollama
# Ctrl+C, then:
ollama serve
```

---

## Security Best Practices

### Development

1. **Never commit `.env` files**
   ```gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use strong SECRET_KEY**
   ```python
   # Generate new key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Keep dependencies updated**
   ```powershell
   pip list --outdated
   npm outdated
   ```

### Production

1. **Set DEBUG=False**
2. **Use environment variables for secrets**
3. **Enable HTTPS**
4. **Set up proper authentication**
5. **Regular security audits**

---

## Support & Resources

### Documentation
- [OLLAMA_RELIABILITY_GUIDE.md](./OLLAMA_RELIABILITY_GUIDE.md)
- [TTS_COMPREHENSIVE_GUIDE.md](./TTS_COMPREHENSIVE_GUIDE.md)
- [QUICK_START.md](./QUICK_START.md)
- [ITERATIVE_IMPLEMENTATION_ROADMAP.md](./ITERATIVE_IMPLEMENTATION_ROADMAP.md)

### Common Commands Reference

```powershell
# Start services
ollama serve                              # Start Ollama
python manage.py runserver 8000          # Start Django
npm start                                 # Start React (from frontend/)

# Testing
python test_ollama_reliability.py        # Test Ollama
python test_mentor_simple.py             # Test mentor chat
python manage.py test                    # Run all Django tests

# Health checks
curl http://localhost:11434/api/tags     # Ollama health
curl http://localhost:8000/api/          # Django health
curl http://localhost:8000/api/mentor/health/  # Mentor service health

# Database
python manage.py migrate                 # Run migrations
python manage.py createsuperuser         # Create admin user
python manage.py shell                   # Django shell

# Cleanup
rm db.sqlite3                            # Reset database
rm -rf frontend/node_modules             # Clean frontend deps
rm -rf venv                              # Clean Python venv
```

---

## Next Steps

After successful startup:

1. ✅ **Explore the Application**
   - Browse lessons
   - Try MentorChat
   - Test TTS features

2. ✅ **Review Documentation**
   - Read implementation guides
   - Understand architecture
   - Review best practices

3. ✅ **Run Tests**
   - Verify Ollama reliability
   - Test all features
   - Check performance

4. ✅ **Customize**
   - Add new lessons
   - Customize teachers
   - Adjust TTS settings

5. ✅ **Deploy** (when ready)
   - Follow DEPLOYMENT_GUIDE.md
   - Set up production environment
   - Configure monitoring

---

**Last Updated**: 2025-11-26  
**Version**: 2.0.0  
**Status**: Production Ready ✅

**Achievement**: Complete end-to-end solution with reliable Ollama connectivity and comprehensive TTS! 🎉
