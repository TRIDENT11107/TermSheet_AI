TermSheet AI is an intelligent system built to automate the extraction and validation of key information from investment term sheets using machine learning and natural language processing (NLP). It streamlines the legal document review process for startups, investors, and legal professionals by identifying critical clauses, flagging inconsistencies, and offering smart suggestions based on learned patterns
<img width="2449" height="1372" alt="image" src="https://github.com/user-attachments/assets/c89c0116-6342-48c2-9421-6a33aac590f7" />
<img width="2317" height="1210" alt="image" src="https://github.com/user-attachments/assets/75457e80-aee7-4870-9359-840093ef7633" />

Features

OCR and PDF extraction for both scanned and native term sheets

NLP-powered clause identification and classification

Automated red-flag detection for important legal or financial terms

Simple web interface for uploading documents and viewing results

Modular backend pipeline for easy maintenance and expansion

Problem Statement

Manually reviewing investment term sheets is time-consuming and prone to human oversight. Non-standard clause wording, missing provisions, or unfavorable terms often go unnoticed. TermSheet AI addresses this by leveraging machine learning to intelligently extract and validate critical elements of term sheets, helping users identify risks and gain insights quickly and efficiently.

Tech Stack

Python, Flask, scikit-learn, spaCy, PyMuPDF, pytesseract, pandas, HTML, CSS, JavaScript

Folder Structure

TERMSHEET AI/ ├── Backend/ │ ├── pycache/ │ │ └── app.cpython-313.pyc │ ├── model/ (ML model files) │ ├── utils/ │ │ ├── pycache/ │ │ ├── nlp_utils.py (natural language processing utilities) │ │ ├── ocr_utils.py (optical character recognition functions) │ │ ├── pdf_utils.py (PDF reading and parsing) │ │ ├── predict.py (model inference logic) │ │ └── preprocess.py (text preprocessing) │ └── app.py (main backend logic using Flask) ├── Datasets/ (sample and training data) ├── Front End/ │ └── index.html (main UI) ├── project_architecture.html (architecture overview) ├── requirements.txt (dependency list) ├── run_app.bat (Windows batch script to run backend) ├── run_app.py (Python launcher script) ├── RUN_ME.bat (alternate run script) ├── simple_app.py (simplified version of the app for testing) ├── standalone.html (alternate frontend UI) └── test-upload.html (document upload test page)

How to Run

Clone the repository: git clone https://github.com/your-username/TermSheet-AI.git

Install the required libraries: pip install -r requirements.txt

Run the application: python run_app.py

Access it in your browser at: http://localhost:5000

Methodology

TermSheet AI uses an end-to-end pipeline that includes:

Preprocessing and cleaning of raw or OCR-extracted text

Tokenization and entity recognition to isolate legal and financial terms

Classification of clauses using a trained machine learning model

Validation logic to flag suspicious, missing, or critical clauses

Key backend components include:

ocr_utils.py for converting scanned images to text using Tesseract

pdf_utils.py for reading and parsing PDFs

preprocess.py for cleaning and preparing data

predict.py for making clause predictions using the ML model

nlp_utils.py for custom NLP tagging and classification rules

Contributions

We welcome suggestions, issues, and pull requests to improve this project. Please ensure major changes are discussed via issues first.

Contact

For queries or collaboration, contact us at rastogisarthak84@gmail.com or open an issue on GitHub.
