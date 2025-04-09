from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import easyocr
from fpdf import FPDF
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # ✅ Fix CORS issues

# Create an upload folder if it doesn't exist
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize EasyOCR reader (CPU optimized)
reader = easyocr.Reader(["en"], gpu=False, quantize=True)

extracted_text = ""  # Store extracted text globally

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract", methods=["POST"])
def extract_text():
    global extracted_text
    logging.info("✅ Received request to extract text")

    if "image" not in request.files:
        logging.error("❌ No image found in request")
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files["image"]
    if image.filename == "":
        logging.error("❌ No file selected")
        return jsonify({"error": "No selected file"}), 400

    # Save the image securely
    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image.save(image_path)
    logging.info(f"✅ Image saved at {image_path}")

    try:
        result = reader.readtext(image_path, detail=0)
        extracted_text = "\n".join(result)
        logging.info(f"✅ Extracted text: {extracted_text}")
        return jsonify({"text": extracted_text})
    except Exception as e:
        logging.error(f"❌ Error in OCR: {e}")
        return jsonify({"error": "Error processing image"}), 500

@app.route("/convert_pdf", methods=["POST"])
def convert_to_pdf():
    global extracted_text
    if not extracted_text:
        return jsonify({"error": "No text to convert"}), 400

    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], "extracted_text.pdf")

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, extracted_text)
        pdf.output(pdf_path)

        if not os.path.exists(pdf_path):
            return jsonify({"error": "PDF file was not created"}), 500

        return jsonify({"pdf_url": f"/uploads/extracted_text.pdf"})
    except Exception as e:
        logging.error(f"❌ Error creating PDF: {e}")
        return jsonify({"error": "Error generating PDF"}), 500

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
