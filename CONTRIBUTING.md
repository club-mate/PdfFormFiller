# Contributing to PDF Form Filler

First off, thank you for considering contributing to PDF Form Filler! It's people like you that make PDF Form Filler such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem** in as many details as possible
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs if possible**
* **Include your environment details** (OS, Python version, etc.)
* **Include logs and error messages**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and the expected behavior**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required template
* Follow the Python styleguides
* Include appropriate test cases
* End all files with a newline
* Avoid platform-dependent code
* Use meaningful commit messages

## Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/PdfFormFiller.git
   cd PdfFormFiller
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"  # Once dev dependencies are added to pyproject.toml
   # Or currently:
   pip install -r requirements.txt
   ```

5. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

6. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** on GitHub

## Styleguides

### Python Code

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
* Use type hints for function arguments and return types
* Write docstrings for all functions and classes
* Keep functions focused and reasonably short
* Use meaningful variable and function names
* Add comments for complex logic

Example:
```python
def extract_form_fields(pdf_path: str) -> List[str]:
    """Extract form field names from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of form field names found in the PDF
    """
    # Implementation here
    pass
```

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an emoji:
  - 🎨 `:art:` Improve code structure/format
  - 🐛 `:bug:` Fix bug
  - 📚 `:books:` Documentation updates
  - ✨ `:sparkles:` Add feature
  - 🚀 `:rocket:` Improve performance
  - ✅ `:white_check_mark:` Add tests
  - 🔒 `:lock:` Security improvements
  - ♻️ `:recycle:` Refactor code

Example:
```
✨ Add PDF encryption support

- Add support for encrypted PDF processing
- Handle user password prompts for encrypted files
- Add tests for encrypted PDF functionality

Closes #42
```

## Testing

* Write tests for new features
* Ensure all tests pass before submitting a PR
* Maintain or improve code coverage
* Run tests locally before pushing:
  ```bash
  python -m pytest
  ```

## Documentation

* Update the README.md if you change functionality
* Add docstrings to new functions and classes
* Update CHANGELOG.md with your changes
* Add comments for complex logic

## Community

* Use the discussions section for questions
* Be respectful and constructive in feedback
* Help other contributors when possible
* Share knowledge and learn from others

## License

By contributing to PDF Form Filler, you agree that your contributions will be licensed under its MIT License.

## Questions?

Feel free to create an issue labeled as a question, or reach out to the maintainers directly.

Thank you for contributing! 🎉
