import logging
import os
import tempfile
import PyPDF2
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        if reader.get_form_text_fields() or hasattr(reader, 'get_fields'):
            # For newer versions of PyPDF2
            if hasattr(reader, 'get_fields'):
                form_fields = reader.get_fields()
            else:
                # For older versions of PyPDF2
                form_fields = reader.get_form_text_fields()
            
            # Extract field names
            for field_name in form_fields:
                fields.append(field_name)
            
            logger.debug(f"Extracted {len(fields)} form fields: {fields}")
            return fields
        else:
            logger.warning("No form fields found in the PDF")
            return []
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
            if page.Annots:
                for annotation in page.Annots:
                    if annotation.T and str(annotation.T) in field_data:
                        field_name = str(annotation.T)
                        annotation.update(
                            PdfDict(V=field_data[field_name], AP=PdfDict())
                        )
        
        writer = PdfWriter()
        writer.write(output_path, reader)
        
        # Double-check if the form was filled by comparing field counts
        check_reader = PyPDF2.PdfReader(output_path)
        if hasattr(check_reader, 'get_fields'):
            check_fields = check_reader.get_fields()
        else:
            check_fields = check_reader.get_form_text_fields()
        
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
            if '/Annots' in page:
                annotations = page['/Annots']
                for annotation in annotations:
                    annot_obj = annotation.get_object()
                    if annot_obj.get('/Subtype') == '/Widget' and '/T' in annot_obj:
                        field_name = annot_obj['/T']
                        if field_name in field_data:
                            rect = annot_obj['/Rect']
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
                    x1, y1, x2, y2 = info['rect']
                    
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
