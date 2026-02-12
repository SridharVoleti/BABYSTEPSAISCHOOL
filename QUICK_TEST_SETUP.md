# Quick Test Setup Guide

**Date**: 2025-12-11  
**Author**: BabySteps Development Team

---

## Prerequisites

Ensure you have the following installed:
- **Python 3.9+** with pip
- **Node.js 16+** with npm
- **Git** (for version control)

---

## Installation Steps

### 1. Backend Test Setup (5 minutes)

```powershell
# Navigate to project root
cd d:\Sridhar\Projects\BabyStepsDigitalSchool

# Install Python test dependencies
pip install pytest pytest-django pytest-cov coverage

# Verify pytest is installed
pytest --version

# Run a quick test
python -m pytest tests/ -v --tb=short
```

### 2. Frontend Test Setup (5 minutes)

```powershell
# Navigate to frontend directory
cd frontend

# Install test dependencies (included in package.json)
npm install

# Verify Jest is working
npm test -- --version

# Run a quick test
npm test -- --watchAll=false
```

### 3. Verify Complete Setup (2 minutes)

```powershell
# Return to project root
cd ..

# Run all tests using the automation script
.\run_all_tests.ps1
```

Expected output:
```
🎉 ALL TESTS PASSED! 🎉
```

---

## Quick Commands Reference

### Run All Tests
```powershell
.\run_all_tests.ps1
```

### Run Backend Tests Only
```powershell
python -m pytest tests/ -v
```

### Run Frontend Tests Only
```powershell
cd frontend
npm test
```

### Run Tests with Coverage
```powershell
# Backend
python -m pytest tests/ --cov=services --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```

### Auto-run Tests on File Changes
```powershell
.\run_tests_on_change.ps1
```

---

## Troubleshooting

### Issue: pytest not found
**Solution**: `pip install pytest pytest-django`

### Issue: npm test fails
**Solution**: 
```powershell
cd frontend
rm -r node_modules
npm install
```

### Issue: Database errors
**Solution**: `python manage.py migrate`

### Issue: Ollama tests fail
**Solution**: 
```powershell
# Start Ollama service
ollama serve

# In another terminal, ensure model is available
ollama pull llama3.2
```

---

## What Was Created

### Test Files Created
1. **Backend Tests** (tests/ directory):
   - `test_curriculum_api.py` - 19 API endpoint tests
   - `test_mentor_chat_api.py` - 17 chat API tests
   - `test_models.py` - 14 model tests
   - **Total**: 50 automated backend tests

2. **Frontend Tests** (frontend/src/__tests__/):
   - `LessonViewer.test.js` - 15 component tests
   - `MentorChat.test.js` - 15 chat component tests
   - `TTSService.test.js` - 25 service tests
   - **Total**: 55 automated frontend tests

3. **Documentation**:
   - `TEST_CASES.csv` - 130 documented test cases
   - `TESTING_GUIDE.md` - Comprehensive testing guide
   - `QUICK_TEST_SETUP.md` - This file

4. **Automation Scripts**:
   - `run_all_tests.ps1` - Main test runner
   - `run_tests_on_change.ps1` - File watcher for auto-testing
   - `pre-commit-hook.ps1` - Pre-commit test validation
   - `.github/workflows/test.yml` - CI/CD pipeline

5. **Configuration**:
   - `pytest.ini` - pytest configuration
   - `conftest.py` - Shared test fixtures

---

## Test Coverage Summary

| Component | Tests | Status |
|-----------|-------|--------|
| Backend API | 36 | ✅ Active |
| Backend Models | 14 | ✅ Active |
| Frontend Components | 30 | ✅ Active |
| Frontend Services | 25 | ✅ Active |
| **Total Automated** | **105** | **✅ Active** |
| Integration | 25 | 🔄 Pending |
| **Grand Total** | **130** | - |

---

## Next Actions

### Immediate (Now)
1. ✅ Run `.\run_all_tests.ps1` to verify setup
2. ✅ Review `TEST_CASES.csv` for all test cases
3. ✅ Read `TESTING_GUIDE.md` for detailed documentation

### Short-term (This Week)
1. Set up pre-commit hook for automatic testing
2. Configure GitHub Actions for CI/CD
3. Implement pending integration tests
4. Add performance benchmarks

### Long-term (This Month)
1. Implement security tests
2. Add accessibility tests
3. Create browser compatibility tests
4. Set up automated performance monitoring

---

## Support

For detailed information, see:
- **TESTING_GUIDE.md** - Complete testing documentation
- **TEST_CASES.csv** - All test case details
- **README.md** - Project overview

---

**Setup Complete!** 🎉

You now have a comprehensive automated testing framework that:
- ✅ Runs 105 automated tests
- ✅ Covers backend APIs and models
- ✅ Covers frontend components and services
- ✅ Provides detailed test reports
- ✅ Integrates with CI/CD
- ✅ Supports test-driven development

**Start testing**: `.\run_all_tests.ps1`
