# Updating Tests After Code Changes

**Purpose**: Guide for keeping tests synchronized with code changes  
**Date**: 2025-12-11

---

## When to Update Tests

### After Adding New Features
1. Create new test file or add to existing
2. Write tests for all new endpoints/components
3. Update `TEST_CASES.csv` with new test cases
4. Run tests to verify: `.\run_all_tests.ps1`

### After Modifying Existing Features
1. Update affected test cases
2. Verify tests still pass
3. Update test descriptions in CSV if needed
4. Check coverage hasn't decreased

### After Bug Fixes
1. Add regression test for the bug
2. Ensure test fails with bug present
3. Verify test passes with fix
4. Document in test case comments

---

## Workflow: Test-Driven Development

### Recommended Process
```
1. Write failing test for new feature
2. Implement feature to make test pass
3. Refactor code while keeping tests green
4. Update documentation
5. Run all tests before committing
```

### Example Workflow

```powershell
# 1. Create new test
# Edit: tests/test_new_feature.py
# Add test case that fails

# 2. Run test to verify it fails
python -m pytest tests/test_new_feature.py -v

# 3. Implement feature
# Edit: services/new_feature/views.py

# 4. Run test to verify it passes
python -m pytest tests/test_new_feature.py -v

# 5. Run all tests to ensure nothing broke
.\run_all_tests.ps1

# 6. Update documentation
# Edit: TEST_CASES.csv
# Add: TC-XXX,Backend,New Feature,...

# 7. Commit changes
git add .
git commit -m "Add new feature with tests"
```

---

## Automatic Test Execution

### On Every Code Change
```powershell
# Start file watcher
.\run_tests_on_change.ps1

# Now edit any .py or .js/.jsx/.ts/.tsx file
# Tests will run automatically after 3 seconds
```

### On Every Commit (Pre-commit Hook)
```powershell
# One-time setup
# Copy pre-commit-hook.ps1 to .git/hooks/pre-commit

# Now every git commit will:
# 1. Detect changed files
# 2. Run relevant tests
# 3. Block commit if tests fail
```

### On Every Push (CI/CD)
```
# GitHub Actions automatically runs on push
# View results at: https://github.com/[your-repo]/actions

# Pipeline runs:
# 1. Backend tests (Python 3.9, 3.10, 3.11)
# 2. Frontend tests (Node 16, 18, 20)
# 3. Integration tests
# 4. Coverage reports
```

---

## Maintaining Test Coverage

### Check Current Coverage

```powershell
# Backend coverage
python -m pytest tests/ --cov=services --cov-report=term

# Frontend coverage
cd frontend
npm test -- --coverage
```

### Target Coverage Goals
- **Backend**: > 90% (Current: ~95%)
- **Frontend**: > 80% (Current: ~85%)
- **Critical Paths**: 100%

### When Coverage Drops

1. **Identify uncovered code**:
   ```powershell
   # View HTML report
   python -m pytest tests/ --cov=services --cov-report=html
   start coverage_backend/index.html
   ```

2. **Add tests for uncovered lines**

3. **Verify coverage improved**:
   ```powershell
   python -m pytest tests/ --cov=services --cov-report=term
   ```

---

## Test Case CSV Management

### Adding New Test Cases

1. Open `TEST_CASES.csv`
2. Add new row with next TC-ID (TC-131, TC-132, etc.)
3. Fill in all columns:
   - Test_ID: TC-XXX
   - Category: Backend/Frontend/Integration/etc.
   - Component: What's being tested
   - Test_Name: Descriptive name
   - Description: What the test does
   - Expected_Result: What should happen
   - Priority: High/Medium/Low
   - Status: Active/Pending/Deprecated
   - Automated: Yes/No

### Example CSV Entry
```csv
TC-131,Backend,New API,Test New Endpoint,Verify new endpoint returns data,200 with valid response,High,Active,Yes
```

---

## Common Update Scenarios

### Scenario 1: New API Endpoint Added

```python
# 1. Add test in tests/test_curriculum_api.py
def test_new_endpoint(self):
    """
    TC-131: Test new endpoint
    Expected: Returns expected data
    """
    response = self.client.get('/api/new-endpoint/')
    self.assertEqual(response.status_code, 200)

# 2. Run test
python -m pytest tests/test_curriculum_api.py::TestNewEndpoint::test_new_endpoint -v

# 3. Update CSV
# Add TC-131 row
```

### Scenario 2: Component Behavior Changed

```javascript
// 1. Update test in __tests__/Component.test.js
test('updated behavior', () => {
  // Update expectations to match new behavior
  expect(component).toHaveNewBehavior();
});

// 2. Run test
npm test -- Component.test.js

// 3. Update CSV description if needed
```

### Scenario 3: Bug Fixed

```python
# 1. Add regression test
def test_bug_123_fixed(self):
    """
    TC-132: Regression test for bug #123
    Expected: Bug no longer occurs
    """
    # Test that previously caused bug
    result = buggy_function(edge_case)
    self.assertNotEqual(result, 'bug_value')

# 2. Verify test fails without fix
# 3. Apply fix
# 4. Verify test passes
# 5. Update CSV with regression test
```

---

## Best Practices

### Do's ✅
- Write tests before or alongside code
- Run tests before committing
- Keep tests simple and focused
- Use descriptive test names
- Update CSV for every new test
- Maintain >90% backend coverage
- Maintain >80% frontend coverage
- Document complex test logic

### Don'ts ❌
- Don't skip writing tests
- Don't commit failing tests
- Don't delete tests without good reason
- Don't ignore coverage drops
- Don't forget to update CSV
- Don't write overly complex tests
- Don't test implementation details

---

## Checklist for Updates

Before committing code changes:

- [ ] All existing tests still pass
- [ ] New tests written for new features
- [ ] TEST_CASES.csv updated
- [ ] Coverage hasn't decreased
- [ ] Test names are descriptive
- [ ] Edge cases are covered
- [ ] Documentation updated
- [ ] Pre-commit hook passes

---

## Getting Help

### Test Failures
1. Read the error message carefully
2. Run single failing test with verbose output
3. Check if recent changes affected the test
4. Review test expectations vs actual behavior
5. Ask team if unclear

### Coverage Issues
1. Generate HTML coverage report
2. Identify uncovered lines
3. Determine if lines need testing
4. Add tests for critical uncovered code
5. Update coverage targets if needed

### Performance Issues
1. Use pytest profiling: `pytest --durations=10`
2. Identify slow tests
3. Consider mocking external services
4. Split large test files
5. Use appropriate test fixtures

---

**Remember**: Tests are living documentation. Keep them updated, and they'll keep your code reliable!
