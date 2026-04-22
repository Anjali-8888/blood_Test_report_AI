const CATEGORY_ORDER = ["Diet", "Exercise", "Lifestyle", "Follow-up"];

export default function RecommendationList({ interpretation, recommendations }) {
  const summary = recommendations?.summary;
  const keyPoints = recommendations?.key_points || [];
  const urgentFlags = recommendations?.urgent_flags || [];
  const items = recommendations?.recommendations || [];
  const disclaimer = recommendations?.disclaimer;

  const grouped = CATEGORY_ORDER.map((category) => ({
    category,
    items: items.filter((item) => item.category === category),
  })).filter((group) => group.items.length > 0);

  return (
    <section className="recommendation-stack">
      {interpretation?.rule_based_insights?.length > 0 && (
        <div className="panel">
          <p className="eyebrow">Interpretation</p>
          <h3 className="section-subtitle">Rule-based clinical insights</h3>
          <ul className="insight-list">
            {interpretation.rule_based_insights.map((insight) => (
              <li key={insight}>{insight}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="panel">
        <p className="eyebrow">Recommendations</p>
        <h3 className="section-subtitle">General wellness guidance</h3>
        <p className="summary-text">{summary}</p>
        {keyPoints.length > 0 && (
          <ul className="insight-list compact">
            {keyPoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        )}
      </div>

      {urgentFlags.length > 0 && (
        <div className="urgent-box">
          <h4>Urgent flags</h4>
          <ul>
            {urgentFlags.map((flag) => (
              <li key={flag}>{flag}</li>
            ))}
          </ul>
        </div>
      )}

      {grouped.map((group) => (
        <div className="panel" key={group.category}>
          <h4 className="category-title">{group.category}</h4>
          <div className="recommendation-grid">
            {group.items.map((item) => (
              <article className="recommendation-card" key={`${group.category}-${item.title}`}>
                <div className="recommendation-head">
                  <strong>{item.title}</strong>
                  <span className={`priority-pill ${item.priority}`}>{item.priority}</span>
                </div>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
        </div>
      ))}

      <p className="supporting-copy">{disclaimer}</p>
    </section>
  );
}
