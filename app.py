from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import re

app = Flask(__name__)

# Set up the path to Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Upload folder configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Check if the file is allowed (by extension)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to display the index page
@app.route('/')
def index():
    return render_template('index.html')

# Function to parse the OCR output into a structured dictionary

def is_gibberish(line):
    # Check if the line has too many non-alphabetic characters
    non_alpha_count = len(re.findall(r'[^a-zA-Z\s]', line))
    # Check if more than half the line is non-alphabetic
    return non_alpha_count > len(line) / 2

def parse_ocr_output(text):
    # Initialize the dictionary with the desired structure
    details = {
        "Certification": "",
        "CertificationDesignations": "",
        "IssuedTo": "",
        "Issued": "",
        "Expires": ""
    }

    # Split the text into lines and iterate
    lines = text.split('\n')

    for line in lines:
        line = line.strip()  # Clean up the line

        # Skip irrelevant or noisy lines
        if len(line) < 3 or "committed" in line.lower() or "quality" in line.lower():
            continue

        # Look for patterns in the lines
        if "Certification" in line and "Designations" not in line:
            # Match certification number using regex
            match = re.search(r'Certificaton #\s*(\S+)', line)
            if match:
                details["Certification"] = match.group(1)

        elif "Certification Designations" in line:
            # Extract the Certification Designations
            parts = line.split(":")
            if len(parts) > 1:
                details["CertificationDesignations"] = parts[1].strip()

        elif re.search(r"Issued To", line, re.IGNORECASE):
            # Extract the name of the person the certificate is issued to
            details["IssuedTo"] = line.split(":")[1].strip()

        elif re.search(r"Issued", line, re.IGNORECASE) and re.search(r"Expires", line, re.IGNORECASE):
            # Use regex to match the Issued and Expires dates in a single line
            date_match = re.search(r"Issued:\s*([\d/]+)\s*Expires:\s*([\d/]+)", line)
            if date_match:
                details["Issued"] = date_match.group(1)
                details["Expires"] = date_match.group(2)

    return details

# Route to handle file uploads and OCR processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Secure and save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Perform OCR on the uploaded image
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)

        # Parse the OCR text into structured data
        details = parse_ocr_output(text)
        # print(details)

        # Pass both the extracted text and the parsed details to the template
        return render_template('index.html', extracted_text=text, details=details)

    return redirect(url_for('index'))

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
