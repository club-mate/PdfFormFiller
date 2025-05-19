# PDF Form Processor

A Python-based tool that extracts form fields from PDFs, stores entries in a database, and generates filled PDFs with PNG conversion.

## Features

- Upload PDF templates with fillable form fields
- Extract form fields automatically from PDF documents
- Fill out forms through a web interface or command-line tool
- Store form data in a SQLite database
- Generate filled PDFs and PNG previews
- View and download completed forms

## Installation

### Prerequisites

- Python 3.8 or higher
- The following Python packages:
  - Flask
  - Flask-SQLAlchemy
  - PyPDF2
  - pdfrw
  - pdf2image
  - reportlab
  - gunicorn (for production deployment)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pdf-form-processor.git
   cd pdf-form-processor
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```
   
   For production environments, use gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Usage

### Web Interface

1. **Launch the application** and navigate to `http://localhost:5000` in your web browser.

2. **Upload a PDF template**:
   - Click on the "Upload PDF Form Template" section
   - Enter a name for your template
   - Select a PDF file with fillable form fields
   - Click "Upload"

3. **Fill out a form**:
   - Select a template from the list
   - Click the "Fill Form" button
   - Enter data for each field
   - Click "Submit and Generate PDF"

4. **View and download filled forms**:
   - Navigate to the "Filled Forms" page
   - Preview generated forms
   - Download as PDF or PNG
   - Delete forms when no longer needed

### Command Line Interface

This repository includes a command-line tool for working with PDF forms without using the web interface.

#### Basic Usage

```
./pdf_form_filler.sh [options] [pdf_file]
```

#### Options

- `pdf_file`: Path to a PDF file with form fields
- `--list-templates` or `-l`: List all saved templates and fill one out
- `--list-forms` or `-f`: View all filled forms and their data
- `--help` or `-h`: Display help information

#### Examples

1. **Scan a new PDF and fill out the form**:
   ```
   ./pdf_form_filler.sh example.pdf
   ```
   This will:
   - Scan the PDF file for form fields
   - Prompt you to enter a name for the template
   - Ask for values for each field
   - Generate a filled PDF and PNG
   - Store the form data in the database

2. **List templates and fill one out**:
   ```
   ./pdf_form_filler.sh --list-templates
   ```
   This shows all saved templates and lets you select one to fill out.

3. **View previously filled forms**:
   ```
   ./pdf_form_filler.sh --list-forms
   ```
   This displays all filled forms and their data.

## Workflow

1. **Upload a PDF** with fillable form fields
2. **Fill out the form** by entering data for each field
3. **Submit the form** to generate the filled PDF and PNG preview
4. **View and download** the generated files

## Technical Details

- SQLite database for storing templates, form fields, and filled forms
- Flask web framework for the web interface
- PyPDF2 and pdfrw for PDF processing
- pdf2image for PDF to PNG conversion
- Bootstrap for responsive UI

## File Structure

```
.
├── app.py            # Flask application setup
├── main.py           # Application entry point
├── models.py         # Database models
├── pdf_processor.py  # PDF processing functions
├── pdf_form_filler.py # Command-line PDF processor script
├── pdf_form_filler.sh # Shell wrapper for command-line tool
├── static/           # Static assets (CSS, JS)
├── templates/        # HTML templates
└── README.md         # This file
```

## Limitations

- Works best with standard PDF form fields
- Complex form layouts might not render perfectly in PNG previews
- Very large PDF files might take longer to process

## License

This project is licensed under the MIT License - see the LICENSE file for details.