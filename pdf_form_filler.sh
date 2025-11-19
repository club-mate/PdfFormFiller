#!/bin/bash
# PDF Form Filler Shell Script
# This script is a wrapper for pdf_form_filler.py

# Make the Python script executable if it's not already
chmod +x pdf_form_filler.py

# Function to display help
display_help() {
    echo "PDF Form Filler - Command Line Tool"
    echo "Usage:"
    echo "  $0 [options] [pdf_file]"
    echo ""
    echo "Options:"
    echo "  -h, --help            Display this help message"
    echo "  -l, --list-templates  List all available PDF templates"
    echo "  -f, --list-forms      List all filled forms"
    echo ""
    echo "Examples:"
    echo "  $0 sample.pdf         Scan a new PDF and fill out the form"
    echo "  $0 --list-templates   List templates and fill out a selected one"
    echo "  $0 --list-forms       View all previously filled forms"
}

# Process command line arguments
case "$1" in
    -h|--help)
        display_help
        exit 0
        ;;
    -l|--list-templates)
        ./pdf_form_filler.py --list-templates
        ;;
    -f|--list-forms)
        ./pdf_form_filler.py --list-forms
        ;;
    "")
        display_help
        ;;
    *)
        # Check if the file exists
        if [ -f "$1" ]; then
            ./pdf_form_filler.py "$1"
        else
            echo "Error: File not found: $1"
            echo ""
            display_help
            exit 1
        fi
        ;;
esac

exit 0