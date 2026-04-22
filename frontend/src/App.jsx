import { useState } from "react";
import BloodMarkerTable from "./components/BloodMarkerTable";
import FileUpload from "./components/FileUpload";
import RecommendationList from "./components/RecommendationList";
import ResultCard from "./components/ResultCard";
import { analyzeReport } from "./services/api";

const MEDICAL_DISCLAIMER =
  "This tool provides general health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.";

export default function App() {
  const [state, setState] = useState("idle");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  const handleAnalyze = async (file, gender) => {
    setState("uploading");
    setError("");

    try {
      const data = await analyzeReport(file, gender);
      setResults(data);
      setState("results");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || "Analysis failed. Please try again.";

      if (err?.code === "ECONNABORTED") {
        setError("Analysis is taking too long. Please retry.");
      } else if (status === 413) {
        setError("File too large. Max 10MB.");
      } else if (status === 400) {
        setError(detail);
      } else {
        setError(detail);
      }

      setState("error");
    }
  };

  const resetApp = () => {
    setResults(null);
    setError("");
    setState("idle");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div>
            <p className="eyebrow">Blood Test Analysis</p>
            <h1 className="brand-title">LabSense</h1>
          </div>
          <div className="topbar-chip">Gemini powered • FastAPI + React</div>
        </div>
      </header>

      <main className="page">
        <section className="hero-panel">
          <div className="hero-grid">
            <div>
              <p className="hero-kicker">Upload. Review. Discuss with your doctor.</p>
              <h2 className="hero-title">Blood report analysis with clear flags and practical wellness guidance.</h2>
              <p className="hero-copy">
                The system extracts blood-marker values from digital PDFs, scanned reports,
                and mixed-layout lab documents, compares them against reference ranges, and
                returns calm, structured health guidance without diagnosing disease.
              </p>
              <div className="hero-badges">
                <span className="hero-badge">Native PDF parsing</span>
                <span className="hero-badge">Gemini document AI</span>
                <span className="hero-badge">Optional HF OCR fallback</span>
              </div>
            </div>

            <div className="hero-sidecard">
              <p className="eyebrow">Designed For</p>
              <div className="hero-stat">CBC, lipid, thyroid, sugar, liver and kidney reports</div>
              <p className="hero-sidecopy">
                Best with digital lab PDFs. Scanned reports can work too when OCR fallback is enabled.
              </p>
            </div>
          </div>
          <div className="disclaimer-banner">{MEDICAL_DISCLAIMER}</div>
        </section>

        {(state === "idle" || state === "uploading") && (
          <FileUpload isLoading={state === "uploading"} onAnalyze={handleAnalyze} />
        )}

        {state === "error" && (
          <section className="message-card error-card">
            <h3>Analysis failed</h3>
            <p>{error}</p>
            <p className="supporting-copy">{MEDICAL_DISCLAIMER}</p>
            <button className="secondary-btn" onClick={resetApp}>
              Analyze another report
            </button>
          </section>
        )}

        {state === "results" && results && (
          <section className="results-stack">
            <div className="results-toolbar">
              <div>
                <p className="eyebrow">Results</p>
                <h2 className="section-title">Analysis complete</h2>
              </div>
              <button className="secondary-btn" onClick={resetApp}>
                Analyze another report
              </button>
            </div>

            <ResultCard
              markers={results.markers}
              patientInfo={results.patient_info}
              summary={results.summary}
              interpretation={results.interpretation}
            />
            <BloodMarkerTable markers={results.markers} />
            <RecommendationList interpretation={results.interpretation} recommendations={results.recommendations} />

            <p className="processing-note">
              Processing time: {results.processing_time_seconds}s. {MEDICAL_DISCLAIMER}
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
