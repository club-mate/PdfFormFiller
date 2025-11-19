#!/usr/bin/env python3
"""
PDF Form Filler - Command Line Interface

This script allows users to:
1. Scan a PDF for fillable form fields
2. Enter values for each form field
3. Save the data to a database
4. Generate a filled PDF and PNG preview
"""

import os
import sys
import argparse
import uuid
import json
from datetime import datetime
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the database path
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'pdf_forms.db')

# Import required libraries
try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    import PyPDF2
    from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
    from pdf2image import convert_from_path
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError as e:
    logger.error(f"Required libraries not found: {str(e)}")
    print(f"Error: Missing required libraries. Please install: {str(e)}")
    print("Try: pip install sqlalchemy PyPDF2 pdfrw pdf2image reportlab")
    sys.exit(1)

# Define Base class for models
Base = declarative_base()

# Define models
class PDFTemplate(Base):
    """Represents a PDF template with fillable form fields."""
    __tablename__ = 'pdf_template'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fields = relationship('FormField', backref='template', cascade='all, delete-orphan')
    filled_forms = relationship('FilledForm', backref='template', cascade='all, delete-orphan')

class FormField(Base):
    """Represents a form field in a PDF template."""
    __tablename__ = 'form_field'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('pdf_template.id'), nullable=False)
    field_name = Column(String(255), nullable=False)
    field_type = Column(String(50), default='text')  # text, checkbox, radio, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class FilledForm(Base):
    """Represents a filled PDF form."""
    __tablename__ = 'filled_form'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('pdf_template.id'), nullable=False)
    pdf_path = Column(String(512))
    png_path = Column(String(512))
    data = Column(Text)  # JSON string of form data
    created_at = Column(DateTime, default=datetime.utcnow)

# Define helper functions for PDF processing
def extract_form_fields(pdf_path):
    """
    Extract form field names from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of form field names
    """
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        fields = []
        
        # Check if the document has a form
        form_fields = {}
        if hasattr(reader, 'get_fields'):
            form_fields = reader.get_fields() or {}
        else:
            form_fields = reader.get_form_text_fields() or {}
        
        # Extract field names
        for field_name in form_fields:
            fields.append(field_name)
        
        logger.debug(f"Extracted {len(fields)} form fields: {fields}")
        return fields
    except Exception as e:
        logger.error(f"Error extracting form fields: {str(e)}")
        raise

def fill_pdf_form(template_path, field_data, output_path):
    """
    Fill a PDF form with data and save it to a new file.
    
    Args:
        template_path (str): Path to the PDF template
        field_data (dict): Dictionary mapping field names to values
        output_path (str): Path to save the filled PDF
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try using pdfrw first (more reliable for forms)
        reader = PdfReader(template_path)
        
        for page in reader.pages:
            if hasattr(page, 'Annots') and page.Annots:
                annotations = list(page.Annots)
                for annotation in annotations:
                    if hasattr(annotation, 'T') and annotation.T and str(annotation.T) in field_data:
                        field_name = str(annotation.T)
                        annotation.update(
                            PdfDict(V=field_data[field_name], AP=PdfDict())
                        )
        
        writer = PdfWriter()
        writer.write(output_path, reader)
        
        # Double-check if the form was filled by comparing field counts
        check_reader = PyPDF2.PdfReader(output_path)
        check_fields = {}
        if hasattr(check_reader, 'get_fields'):
            check_fields = check_reader.get_fields() or {}
        else:
            check_fields = check_reader.get_form_text_fields() or {}
        
        # If pdfrw method didn't work well, try the fallback method with reportlab
        if not check_fields or len(check_fields) != len(field_data):
            logger.warning("pdfrw method didn't fill the form correctly, trying fallback method")
            _fill_pdf_form_fallback(template_path, field_data, output_path)
        
        logger.debug(f"Successfully filled PDF form and saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error filling PDF form: {str(e)}")
        # Try fallback method
        try:
            _fill_pdf_form_fallback(template_path, field_data, output_path)
            return True
        except Exception as e2:
            logger.error(f"Fallback method also failed: {str(e2)}")
            raise

def _fill_pdf_form_fallback(template_path, field_data, output_path):
    """
    Fallback method for filling PDF forms using reportlab.
    
    Args:
        template_path (str): Path to the PDF template
        field_data (dict): Dictionary mapping field names to values
        output_path (str): Path to save the filled PDF
    """
    try:
        # Create a temporary PDF with form field values
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        c = canvas.Canvas(temp_pdf.name, pagesize=letter)
        
        # Extract the coordinates of form fields from the template
        reader = PyPDF2.PdfReader(template_path)
        
        # Coordinates and info for each field
        field_info = {}
        for page_num, page in enumerate(reader.pages):
            annots = page.get('/Annots', [])
            if annots:
                for annotation in annots:
                    if annotation:
                        annot_obj = annotation.get_object()
                        if annot_obj.get('/Subtype') == '/Widget' and '/T' in annot_obj:
                            field_name = annot_obj['/T']
                            if field_name in field_data:
                                rect = annot_obj.get('/Rect', [0, 0, 0, 0])
                                field_info[field_name] = {
                                    'page': page_num,
                                    'rect': rect,
                                    'value': field_data[field_name]
                                }
        
        # Create a new page for each page in the original PDF
        for page_num in range(len(reader.pages)):
            if page_num > 0:
                c.showPage()  # Start a new page
            
            # Add text to the current page
            for field_name, info in field_info.items():
                if info['page'] == page_num:
                    # Get the rectangle coordinates
                    rect = info['rect']
                    if len(rect) >= 4:
                        x1, y1, x2, y2 = rect
                        
                        # Adjust coordinates for reportlab (bottom-left origin)
                        # This is a simplification and might need adjustment
                        x = float(x1)
                        y = float(letter[1] - y2)  # Convert from top-left to bottom-left origin
                        
                        # Add the text
                        c.drawString(x, y, str(info['value']))
        
        c.save()
        
        # Now merge the template and the temporary PDF with text
        output = PyPDF2.PdfWriter()
        template = PyPDF2.PdfReader(template_path)
        overlay = PyPDF2.PdfReader(temp_pdf.name)
        
        # Merge each page
        for i in range(len(template.pages)):
            page = template.pages[i]
            if i < len(overlay.pages):
                page.merge_page(overlay.pages[i])
            output.add_page(page)
        
        # Write the result to the output file
        with open(output_path, 'wb') as f:
            output.write(f)
        
        # Clean up the temporary file
        temp_pdf.close()
        os.unlink(temp_pdf.name)
        
        logger.debug(f"Successfully filled PDF form using fallback method and saved to {output_path}")
    except Exception as e:
        logger.error(f"Error in fallback PDF filling method: {str(e)}")
        raise

def convert_pdf_to_png(pdf_path, png_path):
    """
    Convert a PDF file to PNG format.
    
    Args:
        pdf_path (str): Path to the PDF file
        png_path (str): Path to save the PNG file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert the first page of the PDF to PNG
        images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        
        if not images:
            logger.error("No images generated from PDF")
            return False
        
        # Save the first page as PNG
        images[0].save(png_path, 'PNG')
        logger.debug(f"Successfully converted PDF to PNG and saved to {png_path}")
        return True
    except Exception as e:
        logger.error(f"Error converting PDF to PNG: {str(e)}")
        raise

def setup_database():
    """
    Set up the database connection and create tables if they don't exist.
    
    Returns:
        session: SQLAlchemy session
    """
    try:
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join(tempfile.gettempdir(), 'pdf_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Connect to the database
        engine = create_engine(f"sqlite:///{db_path}")
        
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info(f"Connected to database at {db_path}")
        return session, upload_folder
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        sys.exit(1)

def scan_pdf(pdf_path, session, upload_folder):
    """
    Scan a PDF file for form fields and store it in the database.
    
    Args:
        pdf_path (str): Path to the PDF file
        session: SQLAlchemy session
        upload_folder (str): Path to upload folder
        
    Returns:
        tuple: (template, fields)
    """
    try:
        # Check if file exists and is a PDF
        if not os.path.exists(pdf_path):
            print(f"Error: File not found: {pdf_path}")
            sys.exit(1)
            
        if not pdf_path.lower().endswith('.pdf'):
            print(f"Error: File is not a PDF: {pdf_path}")
            sys.exit(1)
            
        # Extract form fields from the PDF
        print(f"Scanning {pdf_path} for form fields...")
        fields = extract_form_fields(pdf_path)
        
        if not fields:
            print("No form fields found in the PDF.")
            sys.exit(1)
        
        print(f"Found {len(fields)} form fields.")
        
        # Generate a unique filename to avoid collisions
        original_filename = os.path.basename(pdf_path)
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{original_filename}"
        filepath = os.path.join(upload_folder, filename)
        
        # Copy the PDF to the upload folder
        import shutil
        shutil.copy2(pdf_path, filepath)
        
        # Ask for template name
        template_name = input("Enter a name for this PDF template: ")
        if not template_name:
            template_name = original_filename
            
        # Save template information to the database
        template = PDFTemplate(
            name=template_name,
            file_path=filepath,
            original_filename=original_filename
        )
        session.add(template)
        session.commit()
        
        # Add form fields to the database
        for field_name in fields:
            form_field = FormField(
                template_id=template.id,
                field_name=field_name
            )
            session.add(form_field)
        
        session.commit()
        print(f"Successfully saved template: {template_name}")
        
        return template, fields
    except Exception as e:
        logger.error(f"Error scanning PDF: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def fill_template(template, fields, session, upload_folder):
    """
    Prompt for field values and fill out the PDF template.
    
    Args:
        template: PDFTemplate object
        fields: List of form fields
        session: SQLAlchemy session
        upload_folder (str): Path to upload folder
    """
    try:
        # Collect field data
        field_data = {}
        print("\nPlease enter values for each form field:")
        
        for field in fields:
            field_name = field.field_name if hasattr(field, 'field_name') else field
            value = input(f"{field_name}: ")
            field_data[field_name] = value
        
        # Create a filled form record
        filled_form = FilledForm(template_id=template.id)
        session.add(filled_form)
        session.commit()
        
        # Fill the PDF with the form data
        output_pdf_path = os.path.join(
            upload_folder, 
            f"filled_{filled_form.id}_{os.path.basename(template.file_path)}"
        )
        
        print("\nGenerating filled PDF...")
        fill_pdf_form(template.file_path, field_data, output_pdf_path)
        
        # Convert PDF to PNG
        print("Converting PDF to PNG...")
        png_path = output_pdf_path.replace('.pdf', '.png')
        convert_pdf_to_png(output_pdf_path, png_path)
        
        # Update the filled form record with file paths
        filled_form.pdf_path = output_pdf_path
        filled_form.png_path = png_path
        filled_form.data = json.dumps(field_data)  # Store as JSON string
        session.commit()
        
        print("\nForm filled successfully!")
        print(f"PDF saved to: {output_pdf_path}")
        print(f"PNG saved to: {png_path}")
        
    except Exception as e:
        logger.error(f"Error filling PDF: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def list_templates(session):
    """
    List all PDF templates in the database.
    
    Args:
        session: SQLAlchemy session
    """
    try:
        templates = session.query(PDFTemplate).all()
        
        if not templates:
            print("No templates found in the database.")
            return None
        
        print("\nAvailable PDF Templates:")
        print("------------------------")
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.name} ({template.original_filename})")
            print(f"   Created: {template.created_at}")
            print(f"   ID: {template.id}")
            print()
        
        while True:
            choice = input("Enter template number to fill out (or 'q' to quit): ")
            
            if choice.lower() == 'q':
                return None
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    template = templates[index]
                    fields = session.query(FormField).filter_by(template_id=template.id).all()
                    return template, fields
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number or 'q' to quit.")
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        print(f"Error: {str(e)}")
        return None

def list_filled_forms(session):
    """
    List all filled forms in the database.
    
    Args:
        session: SQLAlchemy session
    """
    try:
        filled_forms = session.query(FilledForm).order_by(FilledForm.created_at.desc()).all()
        
        if not filled_forms:
            print("No filled forms found in the database.")
            return
        
        print("\nFilled Forms:")
        print("------------")
        for i, form in enumerate(filled_forms, 1):
            template = session.query(PDFTemplate).get(form.template_id)
            print(f"{i}. Template: {template.name}")
            print(f"   Created: {form.created_at}")
            print(f"   PDF: {form.pdf_path}")
            print(f"   PNG: {form.png_path}")
            
            # Print form data
            if form.data:
                try:
                    data = json.loads(form.data)
                    print("   Data:")
                    for key, value in data.items():
                        print(f"     - {key}: {value}")
                except:
                    print(f"   Data: {form.data}")
            print()
    except Exception as e:
        logger.error(f"Error listing filled forms: {str(e)}")
        print(f"Error: {str(e)}")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='PDF Form Filler - Command Line Interface')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file')
    parser.add_argument('--list-templates', action='store_true', help='List all PDF templates')
    parser.add_argument('--list-forms', action='store_true', help='List all filled forms')
    
    args = parser.parse_args()
    
    # Set up database connection
    session, upload_folder = setup_database()
    
    try:
        if args.list_templates:
            # List templates and optionally fill one out
            result = list_templates(session)
            if result:
                template, fields = result
                fill_template(template, fields, session, upload_folder)
        elif args.list_forms:
            # List filled forms
            list_filled_forms(session)
        elif args.pdf_path:
            # Scan PDF and fill out template
            template, fields = scan_pdf(args.pdf_path, session, upload_folder)
            fill_template(template, fields, session, upload_folder)
        else:
            # If no arguments provided, show help
            parser.print_help()
    finally:
        session.close()

if __name__ == "__main__":
    main()