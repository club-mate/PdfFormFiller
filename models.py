from app import db
from datetime import datetime
import json
from typing import Optional, List, Dict, Any


class PDFTemplate(db.Model):
    """Represents a PDF template with fillable form fields.

    This model stores information about uploaded PDF templates that contain
    fillable form fields. Each template can have multiple form fields and
    multiple filled instances.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    file_path = db.Column(db.String(512), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    fields: db.relationship = db.relationship(
        'FormField',
        backref='template',
        cascade='all, delete-orphan',
        lazy='joined'
    )
    filled_forms: db.relationship = db.relationship(
        'FilledForm',
        backref='template',
        cascade='all, delete-orphan',
        lazy='select'
    )

    def __repr__(self) -> str:
        """String representation of PDFTemplate."""
        return f"<PDFTemplate {self.id}: {self.name}>"


class FormField(db.Model):
    """Represents a form field in a PDF template.

    This model stores metadata about individual form fields found in a PDF template,
    including the field name and type.
    """
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('pdf_template.id'),
        nullable=False,
        index=True
    )
    field_name = db.Column(db.String(255), nullable=False, index=True)
    field_type = db.Column(db.String(50), default='text')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation of FormField."""
        return f"<FormField {self.id}: {self.field_name} ({self.field_type})>"


class FilledForm(db.Model):
    """Represents a filled PDF form.

    This model stores information about completed forms generated from templates,
    including references to the generated PDF and PNG files, and the form data
    as JSON.
    """
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('pdf_template.id'),
        nullable=False,
        index=True
    )
    pdf_path = db.Column(db.String(512))
    png_path = db.Column(db.String(512))
    data = db.Column(db.Text)  # JSON string of form data
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def get_data(self) -> Dict[str, Any]:
        """Parse and return form data as dictionary.

        Returns:
            dict: Form field data, empty dict if data is None or invalid JSON
        """
        if not self.data:
            return {}
        try:
            return json.loads(self.data)
        except (json.JSONDecodeError, TypeError):
            # Fall back to old string representation format
            try:
                return eval(self.data)
            except Exception:
                return {}

    def set_data(self, data: Dict[str, Any]) -> None:
        """Store form data as JSON string.

        Args:
            data: Dictionary of form field data to store
        """
        self.data = json.dumps(data, default=str)

    def __repr__(self) -> str:
        """String representation of FilledForm."""
        return f"<FilledForm {self.id}: template_id={self.template_id}>"
