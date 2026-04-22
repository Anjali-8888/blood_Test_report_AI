import { useEffect, useRef, useState } from "react";

const STEPS = [
  "Uploading...",
  "Extracting blood values...",
  "Analyzing results...",
  "Generating recommendations...",
];

const MEDICAL_DISCLAIMER =
  "This tool provides general health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.";

export default function FileUpload({ onAnalyze, isLoading }) {
  const inputRef = useRef(null);
  const timerRef = useRef(null);
  const [file, setFile] = useState(null);
  const [gender, setGender] = useState("unknown");
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      window.clearInterval(timerRef.current);
      setActiveStep(0);
      return;
    }

    timerRef.current = window.setInterval(() => {
      setActiveStep((current) => (current < STEPS.length - 1 ? current + 1 : current));
    }, 2200);

    return () => window.clearInterval(timerRef.current);
  }, [isLoading]);

  const selectFile = (selectedFile) => {
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setFile(null);
      setError(validationError);
      return;
    }
    setFile(selectedFile);
    setError("");
  };

  const handleSubmit = async () => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    await onAnalyze(file, gender);
  };

  return (
    <section className="upload-panel">
      <div
        className={`dropzone ${isDragging ? "dragging" : ""} ${file ? "ready" : ""}`}
        onClick={() => !isLoading && inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          selectFile(event.dataTransfer.files?.[0]);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          hidden
          disabled={isLoading}
          onChange={(event) => selectFile(event.target.files?.[0])}
        />

        {!file && (
          <div className="dropzone-empty">
            <p className="dropzone-title">Drop your blood test PDF here</p>
            <p className="dropzone-copy">
              Or click to browse. Digital PDFs work best, and scanned reports can use OCR fallback when configured.
            </p>
          </div>
        )}

        {file && (
          <div className="file-summary">
            <div>
              <p className="file-name">{file.name}</p>
              <p className="file-meta">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready for analysis</p>
            </div>
            <button
              className="ghost-btn"
              type="button"
              disabled={isLoading}
              onClick={(event) => {
                event.stopPropagation();
                setFile(null);
                setError("");
              }}
            >
              Remove
            </button>
          </div>
        )}
      </div>

      <div className="upload-controls">
        <div className="gender-group">
          <label htmlFor="gender">Gender for range matching</label>
          <select
            id="gender"
            value={gender}
            disabled={isLoading}
            onChange={(event) => setGender(event.target.value)}
          >
            <option value="unknown">Prefer not to say</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>

        <button className="primary-btn" type="button" disabled={isLoading || !file} onClick={handleSubmit}>
          {isLoading ? STEPS[activeStep] : "Analyze report"}
        </button>
      </div>

      <div className="upload-tips">
        <div className="tip-card">
          <strong>Works well with</strong>
          <span>Digital PDFs from SRL, Thyrocare, Metropolis, Apollo, Lal PathLabs</span>
        </div>
        <div className="tip-card">
          <strong>Scanned reports</strong>
          <span>Can be processed when Gemini document understanding or HF OCR fallback is available</span>
        </div>
        <div className="tip-card">
          <strong>Best review flow</strong>
          <span>Check the marker table first, then use the summary and recommendations as a guide</span>
        </div>
      </div>

      {isLoading && (
        <div className="progress-panel">
          <div className="progress-bar">
            <span style={{ width: `${((activeStep + 1) / STEPS.length) * 100}%` }} />
          </div>
          <div className="progress-steps">
            {STEPS.map((step, index) => (
              <div key={step} className={`progress-step ${index <= activeStep ? "active" : ""}`}>
                {step}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && <p className="inline-error">{error}</p>}
      <p className="supporting-copy">{MEDICAL_DISCLAIMER}</p>
    </section>
  );
}

function validateFile(file) {
  if (!file) {
    return "Please select a PDF file.";
  }
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    return "Only PDF files are supported.";
  }
  if (file.size > 10 * 1024 * 1024) {
    return "File too large. Max 10MB.";
  }
  return "";
}
