import { useMemo, useRef, useState } from "react";

type Sentiment = {
  polarity: number;
  subjectivity: number;
};

type FinalAssessment = {
  label: string;
  confidence_band: string;
  structure_score: number;
};

type StructureValidation = {
  schema?: string;
  likely_real_structure?: boolean;
  structure_score?: number;
  matched_sections?: string[];
  missing_sections?: string[];
  warnings?: string[];
};

type PredictionResponse = {
  prediction?: string;
  model_confidence?: number | null;
  confidence_method?: string | null;
  class_probabilities?: Record<string, number> | null;
  entities?: string[];
  sentiment?: Sentiment;
  final_assessment?: FinalAssessment;
  structure_validation?: StructureValidation;
  input?: {
    filename?: string | null;
    extension?: string | null;
    source_type?: string | null;
    text_length?: number;
    warnings?: string[];
  };
  error?: string;
};

const SUPPORTED_EXTENSIONS = [
  "pdf",
  "docx",
  "xls",
  "xlsx",
  "txt",
  "csv",
  "png",
  "jpg",
  "jpeg",
  "bmp",
  "tiff",
];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const buildApiUrl = (path: string): string => {
  if (!API_BASE_URL) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
};

const FEATURE_CARDS = [
  {
    icon: "AI",
    title: "AI-Powered Extraction",
    description:
      "Advanced OCR and NLP technologies accurately extract data from structured and unstructured term sheets.",
  },
  {
    icon: "OK",
    title: "Automated Validation",
    description:
      "Rule and model-based checks validate extracted data against defined legal and structural expectations.",
  },
  {
    icon: "AN",
    title: "Detailed Analytics",
    description:
      "Comprehensive reports provide section-level findings, confidence, and warning signals for review.",
  },
  {
    icon: "RT",
    title: "Real-Time Processing",
    description:
      "Process term sheets in seconds and surface likely real/fake outcomes for fast triage.",
  },
  {
    icon: "SC",
    title: "Secure and Compliant",
    description:
      "Backend APIs are isolated and can be integrated with enterprise controls and audit logging.",
  },
  {
    icon: "CL",
    title: "Continuous Learning",
    description:
      "The model improves over time with corrected labels and validated production feedback.",
  },
];

const STEPS = [
  {
    title: "Upload",
    description: "Upload a term sheet in PDF, image, text, or office formats.",
  },
  {
    title: "Extract",
    description: "The backend extracts text using OCR/PDF parsing where needed.",
  },
  {
    title: "Validate",
    description: "ML and structural checks evaluate real/fake confidence.",
  },
  {
    title: "Review",
    description: "Inspect missing sections, warnings, and model predictions.",
  },
  {
    title: "Decide",
    description: "Accept likely real files and route review-required cases.",
  },
];

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [showFullReport, setShowFullReport] = useState(false);

  const uploadLabel = useMemo(() => {
    if (isUploading) {
      return "Processing...";
    }
    if (selectedFile) {
      return selectedFile.name;
    }
    return "Drag and Drop Your File Here";
  }, [isUploading, selectedFile]);

  const resetFeedback = () => {
    setResult(null);
    setError("");
    setShowFullReport(false);
  };

  const getMainReason = (res: PredictionResponse): string[] => {
    const reasons: string[] = [];
    if (res.final_assessment?.label === "likely_fake") {
      reasons.push(`Flagged as likely fake (${res.final_assessment.confidence_band} confidence)`);
    }
    if (
      res.structure_validation &&
      res.structure_validation.missing_sections &&
      res.structure_validation.missing_sections.length > 0
    ) {
      reasons.push(
        `Missing key sections: ${res.structure_validation.missing_sections.slice(0, 3).join(", ")}${res.structure_validation.missing_sections.length > 3 ? "..." : ""}`
      );
    }
    if (res.structure_validation?.structure_score !== undefined && res.structure_validation.structure_score < 0.3) {
      reasons.push(`Low structure score: ${res.structure_validation.structure_score.toFixed(2)}/1.0`);
    }
    if (res.model_confidence !== null && res.model_confidence !== undefined && res.model_confidence < 0.5) {
      reasons.push(`Low model confidence: ${(res.model_confidence * 100).toFixed(1)}%`);
    }
    return reasons.length > 0 ? reasons : ["See full report for details"];
  };

  const triggerFilePicker = () => {
    fileInputRef.current?.click();
  };

  const onFilePicked = (file: File | null) => {
    if (!file) {
      return;
    }

    const extension = file.name.toLowerCase().split(".").pop() || "";
    if (!SUPPORTED_EXTENSIONS.includes(extension)) {
      setSelectedFile(null);
      setResult(null);
      setError(
        `Unsupported file type: ${extension}. Supported: ${SUPPORTED_EXTENSIONS.join(", ")}`
      );
      return;
    }

    setSelectedFile(file);
    resetFeedback();
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    onFilePicked(file);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    onFilePicked(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file first.");
      triggerFilePicker();
      return;
    }

    setIsUploading(true);
    resetFeedback();

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(buildApiUrl("/predict"), {
        method: "POST",
        body: formData,
      });

      const rawBody = await response.text();
      let payload: PredictionResponse | null = null;
      if (rawBody) {
        try {
          payload = JSON.parse(rawBody) as PredictionResponse;
        } catch {
          payload = null;
        }
      }

      if (!response.ok) {
        if (response.status >= 500 && !payload && !rawBody) {
          throw new Error(
            "Backend is unreachable or crashed. Start backend at http://127.0.0.1:5000 and try again."
          );
        }
        const fallback = rawBody
          ? `Request failed (${response.status}): ${rawBody.slice(0, 180)}`
          : `Request failed with status ${response.status}.`;
        throw new Error(payload?.error || fallback);
      }

      if (!payload) {
        throw new Error("Server returned an empty response.");
      }

      setResult(payload);
    } catch (uploadError) {
      const message =
        uploadError instanceof Error ? uploadError.message : "Unexpected upload error.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleCtaClick = () => {
    document.getElementById("upload")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const polarity = result?.sentiment?.polarity ?? 0;
  const subjectivity = result?.sentiment?.subjectivity ?? 0;

  return (
    <>
      <nav className="navbar">
        <div className="container">
          <div className="logo">
            Term<span>Sheet</span>AI
          </div>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#upload">Upload</a>
            <a href="#contact">Contact</a>
          </div>
          <button className="cta-button" onClick={handleCtaClick}>
            Get Started
          </button>
        </div>
      </nav>

      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1>AI-Powered Term Sheet Validation</h1>
            <p>
              Validate term sheets with a combined ML + structure engine that flags missing
              sections, suspicious patterns, and likely fake documents.
            </p>
            <button className="cta-button" onClick={handleCtaClick}>
              Upload Your Term Sheet
            </button>
          </div>
        </div>
      </section>

      <section className="upload-section" id="upload">
        <div className="container">
          <h2 className="section-title">Validate Your Term Sheets</h2>
          <p className="section-description">
            Upload your term sheet and receive model prediction, structure compliance, and a final
            assessment in seconds.
          </p>

          <div className="upload-container">
            <div
              className={`upload-area ${isDragging ? "dragging" : ""}`}
              onClick={triggerFilePicker}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="upload-icon">DOC</div>
              <div className="upload-text">{uploadLabel}</div>
              <div className="upload-subtext">or click to browse your files</div>
              <div className="file-formats">
                {["PDF", "DOCX", "XLSX", "TXT", "JPG"].map((format) => (
                  <span className="file-format" key={format}>
                    {format}
                  </span>
                ))}
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              id="fileInput"
              onChange={handleFileInputChange}
              accept=".pdf,.docx,.xls,.xlsx,.txt,.csv,.png,.jpg,.jpeg,.bmp,.tiff"
            />

            <div className="buttons">
              <button className="btn btn-primary" onClick={handleUpload} disabled={isUploading}>
                {isUploading ? "Uploading..." : "Upload and Validate"}
              </button>
              <button className="btn btn-secondary" onClick={handleCtaClick}>
                Learn More
              </button>
            </div>
          </div>

          {(result || error) && (
            <div id="results" className="results-card">
              {error && <p className="error-text">Error: {error}</p>}

              {result && !showFullReport && (
                <div className="summary-result">
                  <div
                    className={`verdict-box ${result.final_assessment?.label === "likely_fake" ? "fake" : "real"}`}
                  >
                    <h3 className="verdict-title">
                      Term Sheet is:{" "}
                      <strong>
                        {result.final_assessment?.label === "likely_fake"
                          ? "⚠️ LIKELY FAKE"
                          : "✓ LIKELY REAL"}
                      </strong>
                    </h3>
                    <p className="verdict-confidence">
                      Confidence: <strong>{result.final_assessment?.confidence_band || "medium"}</strong>
                    </p>
                  </div>

                  <div className="reason-box">
                    <h4>Why?</h4>
                    <ul className="reason-list">
                      {getMainReason(result).map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>

                  <button
                    className="btn btn-secondary"
                    onClick={() => setShowFullReport(true)}
                  >
                    View Full Report
                  </button>
                </div>
              )}

              {result && showFullReport && (
                <div className="full-report">
                  <button
                    className="btn btn-tertiary collapse-btn"
                    onClick={() => setShowFullReport(false)}
                  >
                    ← Back to Summary
                  </button>

                  <h3>Full Analysis Report</h3>

                  {result.final_assessment && (
                    <div className="result-block">
                      <h4>Primary Decision (ML + Structure)</h4>
                      <div className="result-panel">
                        <p>
                          Label: <strong>{result.final_assessment.label}</strong>
                        </p>
                        <p>Confidence: {result.final_assessment.confidence_band}</p>
                        <p>
                          Structure Score:{" "}
                          {Number(result.final_assessment.structure_score || 0).toFixed(2)}
                        </p>
                      </div>
                    </div>
                  )}

                  {result.prediction && (
                    <div className="result-block">
                      <h4>Model-Only Signal</h4>
                      <p className="result-chip">{result.prediction}</p>
                      {result.model_confidence !== null && result.model_confidence !== undefined && (
                        <p className="confidence-meta">
                          Model confidence: {(result.model_confidence * 100).toFixed(1)}%
                          {result.confidence_method ? ` (${result.confidence_method})` : ""}
                        </p>
                      )}
                      {result.final_assessment &&
                        result.final_assessment.label.includes("fake") &&
                        result.prediction === "valid" && (
                          <p className="mismatch-warning">
                            Structure checks overruled model-only signal.
                          </p>
                        )}
                    </div>
                  )}

                  {result.input && (
                    <div className="result-block">
                      <h4>Input Metadata</h4>
                      <div className="result-panel">
                        <p>Source Type: {result.input.source_type || "N/A"}</p>
                        <p>Extension: {result.input.extension || "N/A"}</p>
                        <p>Extracted Text Length: {result.input.text_length ?? 0}</p>
                        <p>
                          <strong>Warnings:</strong>{" "}
                          {(result.input.warnings || []).join(" | ") || "None"}
                        </p>
                      </div>
                    </div>
                  )}

                  {result.structure_validation && (
                    <div className="result-block">
                      <h4>Structure Validation</h4>
                      <div className="result-panel">
                        <p>Schema: {result.structure_validation.schema || "N/A"}</p>
                        <p>
                          Likely Real Structure:{" "}
                          {result.structure_validation.likely_real_structure ? "Yes" : "No"}
                        </p>
                        <p>
                          Score:{" "}
                          {Number(result.structure_validation.structure_score || 0).toFixed(2)}
                        </p>
                        <p>
                          <strong>Matched Sections:</strong>{" "}
                          {(result.structure_validation.matched_sections || []).join(", ") ||
                            "None"}
                        </p>
                        <p>
                          <strong>Missing Sections:</strong>{" "}
                          {(result.structure_validation.missing_sections || []).join(", ") ||
                            "None"}
                        </p>
                        <p>
                          <strong>Warnings:</strong>{" "}
                          {(result.structure_validation.warnings || []).join(" | ") || "None"}
                        </p>
                      </div>
                    </div>
                  )}

                  {result.entities && result.entities.length > 0 && (
                    <div className="result-block">
                      <h4>Entities Detected</h4>
                      <ul className="entity-list">
                        {result.entities.map((entity, index) => (
                          <li key={`${entity}-${index}`}>{entity}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.sentiment && (
                    <div className="result-block">
                      <h4>Sentiment Analysis</h4>
                      <div className="result-panel">
                        <p>
                          Polarity: {polarity.toFixed(2)} (
                          {polarity > 0 ? "Positive" : polarity < 0 ? "Negative" : "Neutral"})
                        </p>
                        <p>
                          Subjectivity: {subjectivity.toFixed(2)} (
                          {subjectivity > 0.5 ? "Subjective" : "Objective"})
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      <section className="features-section" id="features">
        <div className="container">
          <h2 className="section-title">Key Features</h2>
          <p className="section-description">
            A practical pipeline for classifying term sheets using both language signals and
            section-level structure checks.
          </p>

          <div className="features-grid">
            {FEATURE_CARDS.map((card) => (
              <div className="feature-card" key={card.title}>
                <div className="feature-icon">{card.icon}</div>
                <h3 className="feature-title">{card.title}</h3>
                <p className="feature-description">{card.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="how-it-works" id="how-it-works">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <p className="section-description">
            Upload, validate, review, and decide with a focused workflow.
          </p>

          <div className="steps-container">
            {STEPS.map((step, index) => (
              <div className="step" key={step.title}>
                <div className="step-number">{index + 1}</div>
                <div className="step-title">{step.title}</div>
                <div className="step-description">{step.description}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="contact-section" id="contact">
        <div className="container">
          <h2 className="section-title">Get in Touch</h2>
          <p className="section-description">
            Have questions or want to collaborate? Reach out to the developer.
          </p>
          
          <div className="contact-card">
            <div className="contact-item">
              <a href="mailto:rastogisarthak84@gmail.com" className="contact-heading-link">
                <h3>Email</h3>
              </a>
              <a href="mailto:rastogisarthak84@gmail.com" className="contact-link">
                rastogisarthak84@gmail.com
              </a>
            </div>
            
            <div className="contact-item">
              <a href="https://www.linkedin.com/in/sarthak-rastogi-951811290/" target="_blank" rel="noopener noreferrer" className="contact-heading-link">
                <h3>LinkedIn</h3>
              </a>
              <a href="https://www.linkedin.com/in/sarthak-rastogi-951811290/" target="_blank" rel="noopener noreferrer" className="contact-link">
                Sarthak Rastogi
              </a>
            </div>
            
            <div className="contact-item">
              <a href="https://github.com/TRIDENT11107" target="_blank" rel="noopener noreferrer" className="contact-heading-link">
                <h3>GitHub</h3>
              </a>
              <a href="https://github.com/TRIDENT11107" target="_blank" rel="noopener noreferrer" className="contact-link">
                TRIDENT11107
              </a>
            </div>
          </div>

          <div className="contact-message">
            <p>Whether you want to report a bug, suggest a feature, or just say hello—I'd love to hear from you!</p>
          </div>
        </div>
      </section>

      <footer>
        <div className="container">
          <div className="footer-content">
            <div className="logo">
              Term<span>Sheet</span>AI
            </div>
            <div className="footer-links">
              <a href="#features">Features</a>
              <a href="#how-it-works">How It Works</a>
              <a href="#contact">Contact</a>
            </div>
            <div className="copyright">2026 TermSheetAI. All rights reserved.</div>
          </div>
        </div>
      </footer>
    </>
  );
}

export default App;
