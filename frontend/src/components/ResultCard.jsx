export default function ResultCard({ patientInfo, summary, markers, interpretation }) {
  const overall = interpretation
    ? { label: formatOverallLabel(interpretation.overall_status), tone: scoreTone(interpretation.health_score) }
    : getOverallStatus(markers || [], summary);
  const total = summary.total_markers || 1;
  const normalPercent = (summary.normal_count / total) * 100;
  const lowPercent = (summary.low_count / total) * 100;
  const highPercent = (summary.high_count / total) * 100;

  return (
    <section className="panel summary-panel">
      <div className="summary-grid">
        <div>
          <p className="eyebrow">Patient</p>
          <h3 className="section-subtitle">Report overview</h3>
          <div className="meta-grid">
            <MetaItem label="Name" value={patientInfo.name || "Not available"} />
            <MetaItem label="Age" value={patientInfo.age || "Not available"} />
            <MetaItem label="Gender" value={patientInfo.gender || "unknown"} />
            <MetaItem label="Report date" value={patientInfo.report_date || "Not available"} />
          </div>
          <div className={`overall-chip ${overall.tone}`}>{overall.label}</div>
          {interpretation && (
            <>
              <div className="score-chip">Health score: {interpretation.health_score}/100</div>
              <p className="clinical-summary">{interpretation.clinical_summary}</p>
            </>
          )}
        </div>

        <div className="donut-card">
          <div
            className="donut-chart"
            style={{
              background: `conic-gradient(
                var(--normal) 0 ${normalPercent}%,
                var(--low) ${normalPercent}% ${normalPercent + lowPercent}%,
                var(--high) ${normalPercent + lowPercent}% 100%
              )`,
            }}
          >
            <div className="donut-hole">
              <strong>{summary.total_markers}</strong>
              <span>markers</span>
            </div>
          </div>
          <div className="legend-list">
            <LegendItem color="var(--normal)" label={`${summary.normal_count} Normal`} />
            <LegendItem color="var(--low)" label={`${summary.low_count} Low`} />
            <LegendItem color="var(--high)" label={`${summary.high_count} High`} />
          </div>
        </div>
      </div>
    </section>
  );
}

function scoreTone(score) {
  if (score >= 90) return "good";
  if (score >= 75) return "watch";
  if (score >= 55) return "warning";
  return "critical";
}

function formatOverallLabel(value) {
  if (!value) return "Unknown";
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getOverallStatus(markers, summary) {
  const severeCount = markers.filter((marker) => marker.severity === "severe").length;
  const abnormalCount = summary.low_count + summary.high_count;

  if (severeCount > 0) {
    return { label: "Consult Doctor Immediately", tone: "critical" };
  }
  if (abnormalCount >= 4) {
    return { label: "Needs Attention", tone: "warning" };
  }
  if (abnormalCount > 0) {
    return { label: "Minor Issues", tone: "watch" };
  }
  return { label: "All Good", tone: "good" };
}

function MetaItem({ label, value }) {
  return (
    <div className="meta-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function LegendItem({ color, label }) {
  return (
    <div className="legend-item">
      <span className="legend-dot" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  );
}
