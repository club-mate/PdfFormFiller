import os
import logging
from typing import Dict, Tuple, Any

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, NotFound
import tempfile
import uuid

# Configure logging from environment variable
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass


# Initialize SQLAlchemy with the Base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CSRF protection
try:
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
except ImportError:
    logger.warning("flask_wtf not installed, CSRF protection disabled")
    csrf = None

# Configure SQLite database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf_forms.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'pdf_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize the app with the extension
db.init_app(app)

# Helper functions
def delete_file_safely(filepath: str) -> bool:
    """Safely delete a file, logging warnings if it fails.

    Args:
        filepath: Path to the file to delete

    Returns:
        bool: True if successful or file doesn't exist, False if deletion failed
    """
    if not filepath or not os.path.exists(filepath):
        return True

    try:
        os.remove(filepath)
        logger.debug(f"Successfully deleted file: {filepath}")
        return True
    except OSError as e:
        logger.warning(f"Could not delete file {filepath}: {str(e)}")
        return False


# Import routes after app is initialized to avoid circular imports
with app.app_context():
    from models import PDFTemplate, FormField, FilledForm
    import pdf_processor

    # Create database tables
    db.create_all()

    @app.route('/')
    def index():
        """Home page showing options to upload a PDF or fill out an existing template."""
        templates = PDFTemplate.query.all()
        return render_template('index.html', templates=templates)

    @app.route('/upload', methods=['POST'])
    def upload_pdf() -> Tuple[str, int]:
        """Handle PDF template upload.

        Validates the uploaded file, extracts form fields, and stores the
        template and field information in the database.

        Returns:
            Redirect response to either fill_form or index page
        """
        if 'pdf_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('index'))

        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('index'))

        if not (file and file.filename.lower().endswith('.pdf')):
            flash('Only PDF files are allowed', 'danger')
            return redirect(url_for('index'))

        # Generate a unique filename to avoid collisions
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # Save the uploaded file
            file.save(filepath)

            # Extract form fields from the PDF
            template_name = request.form.get('template_name', original_filename).strip()
            if not template_name:
                template_name = original_filename

            try:
                fields = pdf_processor.extract_form_fields(filepath)
            except Exception as e:
                delete_file_safely(filepath)
                logger.error(f"Error extracting form fields: {str(e)}")
                flash(f'Error reading PDF: {str(e)}', 'danger')
                return redirect(url_for('index'))

            if not fields:
                delete_file_safely(filepath)
                flash('No form fields found in the PDF', 'warning')
                return redirect(url_for('index'))

            # Save template information to the database
            template = PDFTemplate(
                name=template_name,
                file_path=filepath,
                original_filename=original_filename
            )
            db.session.add(template)
            db.session.flush()  # Get the ID without committing

            # Add form fields to the database
            for field_name in fields:
                form_field = FormField(
                    template_id=template.id,
                    field_name=field_name
                )
                db.session.add(form_field)

            db.session.commit()

            logger.info(f"Successfully uploaded template: {template_name} with {len(fields)} fields")
            flash(f'Successfully uploaded template: {template_name}', 'success')
            return redirect(url_for('fill_form', template_id=template.id))

        except Exception as e:
            db.session.rollback()
            delete_file_safely(filepath)
            logger.error(f"Error processing PDF upload: {str(e)}", exc_info=True)
            flash(f'Error uploading PDF: {str(e)}', 'danger')
            return redirect(url_for('index'))

    @app.route('/template/<int:template_id>')
    def fill_form(template_id):
        """Show the form to fill out for a specific template."""
        template = PDFTemplate.query.get_or_404(template_id)
        fields = FormField.query.filter_by(template_id=template_id).all()
        return render_template('form.html', template=template, fields=fields)

    @app.route('/submit_form/<int:template_id>', methods=['POST'])
    def submit_form(template_id: int) -> Tuple[str, int]:
        """Submit filled form data.

        Validates form data, fills the PDF template, generates a PNG preview,
        and stores the result in the database.

        Args:
            template_id: ID of the PDF template to fill

        Returns:
            Redirect response to view_pdfs or fill_form page
        """
        template = PDFTemplate.query.get_or_404(template_id)

        # Create a filled form record
        filled_form = FilledForm(template_id=template_id)
        db.session.add(filled_form)
        db.session.flush()  # Get the ID without committing

        # Get all form fields for this template
        fields = FormField.query.filter_by(template_id=template_id).all()

        # Prepare field data dictionary
        field_data = {}
        for field in fields:
            value = request.form.get(field.field_name, '').strip()
            field_data[field.field_name] = value

        try:
            # Fill the PDF with the form data
            output_pdf_path = os.path.join(
                app.config['UPLOAD_FOLDER'],
                f"filled_{filled_form.id}_{secure_filename(template.original_filename)}"
            )

            try:
                pdf_processor.fill_pdf_form(template.file_path, field_data, output_pdf_path)
            except Exception as e:
                logger.error(f"Error filling PDF: {str(e)}", exc_info=True)
                raise PDFProcessingError(f"Failed to fill PDF: {str(e)}")

            # Convert PDF to PNG
            png_path = output_pdf_path.replace('.pdf', '.png')
            try:
                pdf_processor.convert_pdf_to_png(output_pdf_path, png_path)
            except Exception as e:
                logger.warning(f"Error converting PDF to PNG: {str(e)}", exc_info=True)
                # Don't fail completely if PNG conversion fails

            # Update the filled form record with file paths and data
            filled_form.pdf_path = output_pdf_path
            filled_form.png_path = png_path
            filled_form.set_data(field_data)  # Store as JSON
            db.session.commit()

            logger.info(f"Successfully filled form {filled_form.id} from template {template_id}")
            flash('Form filled successfully!', 'success')
            return redirect(url_for('view_pdfs'))

        except PDFProcessingError as e:
            db.session.rollback()
            delete_file_safely(output_pdf_path)
            delete_file_safely(png_path)
            flash(str(e), 'danger')
            return redirect(url_for('fill_form', template_id=template_id))
        except Exception as e:
            db.session.rollback()
            delete_file_safely(output_pdf_path)
            delete_file_safely(png_path)
            logger.error(f"Unexpected error filling form: {str(e)}", exc_info=True)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            return redirect(url_for('fill_form', template_id=template_id))

    @app.route('/pdfs')
    def view_pdfs():
        """View all filled PDFs."""
        filled_forms = FilledForm.query.order_by(FilledForm.created_at.desc()).all()
        return render_template('pdfs.html', filled_forms=filled_forms)

    @app.route('/download/<int:form_id>/<filetype>')
    def download_file(form_id, filetype):
        """Download filled PDF or PNG."""
        filled_form = FilledForm.query.get_or_404(form_id)
        
        if filetype == 'pdf':
            filepath = filled_form.pdf_path
            mimetype = 'application/pdf'
        elif filetype == 'png':
            filepath = filled_form.png_path
            mimetype = 'image/png'
        else:
            flash('Invalid file type', 'danger')
            return redirect(url_for('view_pdfs'))
        
        if not os.path.exists(filepath):
            flash('File not found', 'danger')
            return redirect(url_for('view_pdfs'))
        
        filename = os.path.basename(filepath)
        return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=filename)

    @app.route('/delete_template/<int:template_id>', methods=['POST'])
    def delete_template(template_id: int) -> Tuple[str, int]:
        """Delete a PDF template and its associated files.

        Args:
            template_id: ID of the template to delete

        Returns:
            Redirect response to index page
        """
        template = PDFTemplate.query.get_or_404(template_id)

        try:
            # Delete the template file
            delete_file_safely(template.file_path)

            # Delete associated filled forms
            filled_forms = FilledForm.query.filter_by(template_id=template_id).all()
            for form in filled_forms:
                # Delete filled form files
                delete_file_safely(form.pdf_path)
                delete_file_safely(form.png_path)
                db.session.delete(form)

            # Delete form fields (cascade handled by relationship, but explicit for clarity)
            FormField.query.filter_by(template_id=template_id).delete()

            # Delete the template record
            db.session.delete(template)
            db.session.commit()

            logger.info(f"Successfully deleted template {template_id}: {template.name}")
            flash('Template deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting template {template_id}: {str(e)}", exc_info=True)
            flash(f'Error deleting template: {str(e)}', 'danger')

        return redirect(url_for('index'))

    @app.route('/delete_filled_form/<int:form_id>', methods=['POST'])
    def delete_filled_form(form_id: int) -> Tuple[str, int]:
        """Delete a filled form and its associated files.

        Args:
            form_id: ID of the filled form to delete

        Returns:
            Redirect response to view_pdfs page
        """
        filled_form = FilledForm.query.get_or_404(form_id)

        try:
            # Delete files if they exist
            delete_file_safely(filled_form.pdf_path)
            delete_file_safely(filled_form.png_path)

            # Delete the database record
            db.session.delete(filled_form)
            db.session.commit()

            logger.info(f"Successfully deleted filled form {form_id}")
            flash('Filled form deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting filled form {form_id}: {str(e)}", exc_info=True)
            flash(f'Error deleting form: {str(e)}', 'danger')

        return redirect(url_for('view_pdfs'))

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> Tuple[str, int]:
        """Handle 404 errors.

        Args:
            e: The exception that triggered the error

        Returns:
            Error page with 404 status code
        """
        logger.warning(f"404 error: {str(e)}")
        return render_template('base.html', error="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e: Exception) -> Tuple[str, int]:
        """Handle 500 errors.

        Args:
            e: The exception that triggered the error

        Returns:
            Error page with 500 status code
        """
        logger.error(f"500 error: {str(e)}", exc_info=True)
        return render_template('base.html', error="Server error occurred"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
