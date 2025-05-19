import os
import logging

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import tempfile
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
    def upload_pdf():
        """Handle PDF template upload."""
        if 'pdf_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('index'))
        
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('index'))
        
        if file and file.filename.lower().endswith('.pdf'):
            # Generate a unique filename to avoid collisions
            original_filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}_{original_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(filepath)
            
            try:
                # Extract form fields from the PDF
                template_name = request.form.get('template_name', original_filename)
                fields = pdf_processor.extract_form_fields(filepath)
                
                if not fields:
                    flash('No form fields found in the PDF', 'warning')
                    return redirect(url_for('index'))
                
                # Save template information to the database
                template = PDFTemplate(
                    name=template_name,
                    file_path=filepath,
                    original_filename=original_filename
                )
                db.session.add(template)
                db.session.commit()
                
                # Add form fields to the database
                for field_name in fields:
                    form_field = FormField(
                        template_id=template.id,
                        field_name=field_name
                    )
                    db.session.add(form_field)
                
                db.session.commit()
                
                flash(f'Successfully uploaded template: {template_name}', 'success')
                return redirect(url_for('fill_form', template_id=template.id))
                
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}")
                flash(f'Error processing PDF: {str(e)}', 'danger')
                return redirect(url_for('index'))
        else:
            flash('Only PDF files are allowed', 'danger')
            return redirect(url_for('index'))

    @app.route('/template/<int:template_id>')
    def fill_form(template_id):
        """Show the form to fill out for a specific template."""
        template = PDFTemplate.query.get_or_404(template_id)
        fields = FormField.query.filter_by(template_id=template_id).all()
        return render_template('form.html', template=template, fields=fields)

    @app.route('/submit_form/<int:template_id>', methods=['POST'])
    def submit_form(template_id):
        """Submit filled form data."""
        template = PDFTemplate.query.get_or_404(template_id)
        
        # Create a filled form record
        filled_form = FilledForm(template_id=template_id)
        db.session.add(filled_form)
        db.session.commit()
        
        # Get all form fields for this template
        fields = FormField.query.filter_by(template_id=template_id).all()
        
        # Prepare field data dictionary
        field_data = {}
        for field in fields:
            value = request.form.get(field.field_name, '')
            field_data[field.field_name] = value
        
        try:
            # Fill the PDF with the form data
            output_pdf_path = os.path.join(
                app.config['UPLOAD_FOLDER'], 
                f"filled_{filled_form.id}_{secure_filename(template.original_filename)}"
            )
            
            pdf_processor.fill_pdf_form(template.file_path, field_data, output_pdf_path)
            
            # Convert PDF to PNG
            png_path = output_pdf_path.replace('.pdf', '.png')
            pdf_processor.convert_pdf_to_png(output_pdf_path, png_path)
            
            # Update the filled form record with file paths
            filled_form.pdf_path = output_pdf_path
            filled_form.png_path = png_path
            filled_form.data = str(field_data)  # Store as string representation
            db.session.commit()
            
            flash('Form filled successfully!', 'success')
            return redirect(url_for('view_pdfs'))
            
        except Exception as e:
            logger.error(f"Error filling PDF: {str(e)}")
            db.session.delete(filled_form)
            db.session.commit()
            flash(f'Error filling PDF: {str(e)}', 'danger')
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
    def delete_template(template_id):
        """Delete a PDF template and its associated files."""
        template = PDFTemplate.query.get_or_404(template_id)
        
        # Delete the file if it exists
        if os.path.exists(template.file_path):
            try:
                os.remove(template.file_path)
            except:
                logger.warning(f"Could not delete file: {template.file_path}")
        
        # Delete associated filled forms
        filled_forms = FilledForm.query.filter_by(template_id=template_id).all()
        for form in filled_forms:
            # Delete filled form files
            for path in [form.pdf_path, form.png_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        logger.warning(f"Could not delete file: {path}")
            
            db.session.delete(form)
        
        # Delete form fields
        FormField.query.filter_by(template_id=template_id).delete()
        
        # Delete the template record
        db.session.delete(template)
        db.session.commit()
        
        flash('Template deleted successfully', 'success')
        return redirect(url_for('index'))

    @app.route('/delete_filled_form/<int:form_id>', methods=['POST'])
    def delete_filled_form(form_id):
        """Delete a filled form and its associated files."""
        filled_form = FilledForm.query.get_or_404(form_id)
        
        # Delete files if they exist
        for path in [filled_form.pdf_path, filled_form.png_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    logger.warning(f"Could not delete file: {path}")
        
        # Delete the database record
        db.session.delete(filled_form)
        db.session.commit()
        
        flash('Filled form deleted successfully', 'success')
        return redirect(url_for('view_pdfs'))

    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        return render_template('base.html', error="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors."""
        return render_template('base.html', error="Server error occurred"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
