# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive type hints throughout codebase
- Custom exception classes for better error handling
- Database indices for improved query performance
- CSRF protection via Flask-WTF
- JSON-based form data storage
- Environment-based logging configuration
- `.gitignore` file for Python artifacts
- GitHub community standards documentation
  - CODE_OF_CONDUCT.md
  - CONTRIBUTING.md
  - SECURITY.md
  - Issue templates
  - Pull request template

### Changed
- Refactored file deletion logic into reusable helper function
- Improved error handling with specific exception types
- Enhanced logging with better formatting and context
- Better input validation and sanitization
- Improved PDF processing with multiple fallback strategies

### Fixed
- Proper database transaction handling with rollback on errors
- Better error messages for debugging

## [1.0.0] - 2024-11-16

### Added
- Initial release of PDF Form Filler
- Web interface for PDF form processing
  - Upload PDF templates
  - Extract form fields automatically
  - Fill forms through web UI
  - Download filled PDFs and PNG previews
  - View and manage form submissions
- Command-line interface
  - Process PDFs from terminal
  - Batch operations support
  - Interactive form filling
- Database storage
  - SQLite database for templates and form data
  - Support for multiple templates and submissions
- PDF processing capabilities
  - Extract form fields from PDFs
  - Fill PDF forms with data
  - Convert PDFs to PNG images
  - Support for encrypted PDFs
- Responsive web interface
  - Bootstrap 5 styling
  - Mobile-friendly design
- Docker and Replit deployment support

## [0.1.0] - 2024-11-01

### Added
- Initial project setup
- Basic Flask application structure
- Database models for PDFTemplate, FormField, and FilledForm
- PDF processing functions
- Basic web interface templates

---

## Guide for Contributors

When adding a new entry to this changelog:

1. **Format**: Use the format specified above
2. **Sections**: Use these standard sections as needed:
   - Added: New features
   - Changed: Changes to existing functionality
   - Deprecated: Soon-to-be removed features
   - Removed: Removed features
   - Fixed: Bug fixes
   - Security: Security improvements and vulnerability patches
3. **Links**: Add links to issues/PRs at the bottom of each version
4. **Date**: Use YYYY-MM-DD format for released versions
5. **Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)

Example pull request:

```markdown
### Added
- New feature description

### Fixed
- Bug fix description

Fixes #123, Closes #456
```

## Version Numbering

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

For more information, see [Semantic Versioning](https://semver.org/).
