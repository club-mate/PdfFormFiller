from app import db
from datetime import datetime

class PDFTemplate(db.Model):
    """Represents a PDF template with fillable form fields."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fields = db.relationship('FormField', backref='template', cascade='all, delete-orphan')
    filled_forms = db.relationship('FilledForm', backref='template', cascade='all, delete-orphan')

class FormField(db.Model):
    """Represents a form field in a PDF template."""
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('pdf_template.id'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(50), default='text')  # text, checkbox, radio, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FilledForm(db.Model):
    """Represents a filled PDF form."""
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('pdf_template.id'), nullable=False)
    pdf_path = db.Column(db.String(512))
    png_path = db.Column(db.String(512))
    data = db.Column(db.Text)  # JSON string of form data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
