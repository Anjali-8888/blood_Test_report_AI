const SEVERITY_RANK = {
  severe: 3,
  moderate: 2,
  mild: 1,
  null: 0,
  undefined: 0,
};

const STATUS_LABELS = {
  normal: "Normal",
  low: "Low",
  high: "High",
  unknown: "Unknown",
};

export default function BloodMarkerTable({ markers }) {
  if (!markers?.length) {
    return (
      <section className="panel">
        <h3 className="section-subtitle">Blood markers</h3>
        <p className="supporting-copy">No recognizable blood test values found.</p>
      </section>
    );
  }

  const sortedMarkers = [...markers].sort((a, b) => compareMarkers(a, b));

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Markers</p>
          <h3 className="section-subtitle">Blood marker table</h3>
        </div>
      </div>

      <div className="table-shell">
        <table className="marker-table">
          <thead>
            <tr>
              <th>Marker</th>
              <th>Your Value</th>
              <th>Normal Range</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedMarkers.map((marker) => (
              <tr key={`${marker.key}-${marker.value}`}>
                <td>{marker.name}</td>
                <td>
                  {marker.value} {marker.unit}
                </td>
                <td>{marker.normal_range}</td>
                <td>
                  <span className={`status-pill ${marker.status}`}>
                    {marker.status === "normal" && marker.borderline
                      ? "Normal (Borderline)"
                      : STATUS_LABELS[marker.status]}
                    {marker.severity ? ` (${capitalize(marker.severity)})` : ""}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function compareMarkers(a, b) {
  const aAbnormal = a.status === "high" || a.status === "low";
  const bAbnormal = b.status === "high" || b.status === "low";

  if (aAbnormal !== bAbnormal) {
    return aAbnormal ? -1 : 1;
  }

  const severityDifference =
    (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0);
  if (severityDifference !== 0) {
    return severityDifference;
  }

  if (a.status !== b.status) {
    if (a.status === "high") return -1;
    if (b.status === "high") return 1;
    if (a.status === "low") return -1;
    if (b.status === "low") return 1;
  }

  return a.name.localeCompare(b.name);
}

function capitalize(value) {
  return value ? value[0].toUpperCase() + value.slice(1) : "";
}
