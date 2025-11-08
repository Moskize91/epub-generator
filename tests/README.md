# Tests

This directory contains the test suite for epub-generator.

## Structure

```
tests/
├── __init__.py         # Package initialization
├── conftest.py         # Test configuration and setup
├── test_generate_epub.py  # Smoke tests for generate_epub
├── asset/              # Test assets (tracked by git)
│   └── test_cover.png  # Sample cover image
└── temp/               # Temporary test files (ignored by git)
```

## Running Tests

Run all tests:
```bash
python test.py
```

Run specific test file:
```bash
python test.py test_generate_epub
```

## Adding New Tests

1. Create test files with `test_*.py` naming pattern
2. Place test assets in `tests/asset/`
3. Use `tests/temp/` for temporary files generated during testing
4. The `temp/` directory is automatically cleaned before each test run

## Current Test Coverage

- **test_generate_epub.py**: Basic smoke tests
  - Minimal EPUB generation
  - EPUB with cover image
  - EPUB with nested chapter structure

## Notes

- Tests are focused on smoke testing rather than comprehensive coverage
- The `temp/` directory is git-ignored and cleaned on each test run
- Test assets in `asset/` are committed to the repository
