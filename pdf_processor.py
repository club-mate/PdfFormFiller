import logging
import os
import tempfile
from typing import List, Dict, Any
import PyPDF2
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path

# Configure logging from environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Exception raised when PDF field extraction fails."""
    pass


class PDFFillingError(Exception):
    """Exception raised when PDF filling fails."""
    pass


class PDFConversionError(Exception):
    """Exception raised when PDF to image conversion fails."""
    pass

def extract_form_fields(pdf_path: str) -> List[str]:
    """Extract form field names from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of form field names found in the PDF

    Raises:
        PDFExtractionError: If PDF reading or field extraction fails
    """
    if not os.path.exists(pdf_path):
        raise PDFExtractionError(f"PDF file not found: {pdf_path}")

    try:
        reader = PyPDF2.PdfReader(pdf_path)
        fields = []

        # Try to get form fields using the best available method
        try:
            if hasattr(reader, 'get_fields') and reader.get_fields():
                form_fields = reader.get_fields()
                fields.extend(form_fields.keys())
            elif hasattr(reader, 'get_form_text_fields'):
                form_fields = reader.get_form_text_fields()
                if form_fields:
                    fields.extend(form_fields.keys() if isinstance(form_fields, dict) else form_fields)
        except Exception as e:
            logger.warning(f"Standard field extraction failed: {str(e)}, trying fallback method")
            # Fallback: extract fields from annotations
            try:
                for page in reader.pages:
                    if '/Annots' in page:
                        for annot in page['/Annots']:
                            try:
                                annot_obj = annot.get_object()
                                if '/T' in annot_obj:
                                    field_name = str(annot_obj['/T']).strip("()")
                                    if field_name not in fields:
                                        fields.append(field_name)
                            except Exception as inner_e:
                                logger.debug(f"Could not extract annotation: {inner_e}")
            except Exception as fallback_e:
                logger.warning(f"Fallback field extraction also failed: {fallback_e}")

        if fields:
            logger.info(f"Extracted {len(fields)} form fields from PDF")
        else:
            logger.warning("No form fields found in the PDF")

        return fields

    except PDFExtractionError:
        raise
    except Exception as e:
        logger.error(f"Error extracting form fields from {pdf_path}: {str(e)}", exc_info=True)
        raise PDFExtractionError(f"Failed to extract form fields: {str(e)}")

def fill_pdf_form(template_path: str, field_data: Dict[str, Any], output_path: str) -> bool:
    """Fill a PDF form with data and save it to a new file.

    This function attempts to fill a PDF form using pdfrw first, then falls back
    to reportlab if the initial method doesn't work.

    Args:
        template_path: Path to the PDF template
        field_data: Dictionary mapping field names to values
        output_path: Path to save the filled PDF

    Returns:
        True if successful

    Raises:
        PDFFillingError: If both primary and fallback methods fail
    """
    if not os.path.exists(template_path):
        raise PDFFillingError(f"Template PDF not found: {template_path}")

    if not field_data:
        logger.warning("No form data provided, copying template as-is")
        field_data = {}

    try:
        # Try using pdfrw first (more reliable for native PDF forms)
        reader = PdfReader(template_path)

        filled_count = 0
        for page in reader.pages:
            if page.Annots:
                for annotation in page.Annots:
                    if hasattr(annotation, 'T') and annotation.T:
                        field_name = str(annotation.T).strip("()")
                        if field_name in field_data:
                            annotation.update(
                                PdfDict(V=field_data[field_name], AP=PdfDict())
                            )
                            filled_count += 1

        writer = PdfWriter()
        writer.write(output_path, reader)

        logger.info(f"Successfully filled {filled_count} fields in PDF and saved to {output_path}")
        return True

    except PDFFillingError:
        raise
    except Exception as e:
        logger.warning(f"pdfrw method failed ({str(e)}), trying fallback method")
        try:
            _fill_pdf_form_fallback(template_path, field_data, output_path)
            logger.info(f"Successfully filled PDF using fallback method and saved to {output_path}")
            return True
        except Exception as fallback_error:
            logger.error(f"Both PDF filling methods failed: {str(fallback_error)}", exc_info=True)
            raise PDFFillingError(f"Failed to fill PDF form: {str(fallback_error)}")

def _fill_pdf_form_fallback(template_path: str, field_data: Dict[str, Any], output_path: str) -> None:
    """Fallback method for filling PDF forms using reportlab overlay.

    This method creates a temporary PDF with text overlays and merges it with
    the template PDF. Used when native PDF form filling doesn't work.

    Args:
        template_path: Path to the PDF template
        field_data: Dictionary mapping field names to values
        output_path: Path to save the filled PDF

    Raises:
        PDFFillingError: If the fallback method fails
    """
    temp_pdf = None
    try:
        # Create a temporary PDF with form field values
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_pdf_name = temp_pdf.name
        temp_pdf.close()

        c = canvas.Canvas(temp_pdf_name, pagesize=letter)

        # Extract the coordinates of form fields from the template
        reader = PyPDF2.PdfReader(template_path)

        # Collect field information for each page
        field_info = {}
        for page_num, page in enumerate(reader.pages):
            if '/Annots' in page:
                annotations = page['/Annots']
                for annotation in annotations:
                    try:
                        annot_obj = annotation.get_object()
                        if annot_obj.get('/Subtype') == '/Widget' and '/T' in annot_obj:
                            field_name = str(annot_obj['/T']).strip("()")
                            if field_name in field_data:
                                rect = annot_obj.get('/Rect', [0, 0, 0, 0])
                                field_info[field_name] = {
                                    'page': page_num,
                                    'rect': rect,
                                    'value': field_data[field_name]
                                }
                    except Exception as e:
                        logger.debug(f"Could not process annotation: {e}")

        # Create text overlay pages
        for page_num in range(len(reader.pages)):
            if page_num > 0:
                c.showPage()

            # Add text for fields on this page
            for field_name, info in field_info.items():
                if info['page'] == page_num:
                    try:
                        rect = info['rect']
                        x1, y1, x2, y2 = [float(v) for v in rect]

                        # Adjust coordinates for reportlab (bottom-left origin)
                        x = x1
                        y = float(letter[1] - y2)

                        # Add the text
                        c.drawString(x, y, str(info['value']))
                    except Exception as e:
                        logger.warning(f"Could not draw field '{field_name}': {e}")

        c.save()

        # Merge the template and the temporary PDF with text
        output = PyPDF2.PdfWriter()
        template = PyPDF2.PdfReader(template_path)
        overlay = PyPDF2.PdfReader(temp_pdf_name)

        # Merge each page
        for i in range(len(template.pages)):
            page = template.pages[i]
            if i < len(overlay.pages):
                page.merge_page(overlay.pages[i])
            output.add_page(page)

        # Write the result to the output file
        with open(output_path, 'wb') as f:
            output.write(f)

        logger.info(f"Successfully filled PDF using fallback method")

    except Exception as e:
        logger.error(f"Error in fallback PDF filling method: {str(e)}", exc_info=True)
        raise PDFFillingError(f"Fallback method failed: {str(e)}")
    finally:
        # Clean up the temporary file
        if temp_pdf:
            try:
                os.unlink(temp_pdf_name)
            except Exception as e:
                logger.debug(f"Could not delete temporary file: {e}")

def convert_pdf_to_png(pdf_path: str, png_path: str) -> bool:
    """Convert the first page of a PDF file to PNG format.

    Args:
        pdf_path: Path to the PDF file
        png_path: Path to save the PNG file

    Returns:
        True if successful

    Raises:
        PDFConversionError: If PDF to PNG conversion fails
    """
    if not os.path.exists(pdf_path):
        raise PDFConversionError(f"PDF file not found: {pdf_path}")

    try:
        # Convert the first page of the PDF to PNG with reasonable DPI
        images = convert_from_path(
            pdf_path,
            dpi=150,
            first_page=1,
            last_page=1,
            fmt='png'
        )

        if not images:
            raise PDFConversionError("No images generated from PDF")

        # Save the first page as PNG
        images[0].save(png_path, 'PNG')
        logger.info(f"Successfully converted PDF to PNG and saved to {png_path}")
        return True

    except PDFConversionError:
        raise
    except Exception as e:
        logger.error(f"Error converting PDF to PNG: {str(e)}", exc_info=True)
        raise PDFConversionError(f"Failed to convert PDF to PNG: {str(e)}")
