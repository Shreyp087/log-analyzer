import type { UploadResponse } from "@/types";

type SummaryCardsProps = {
  result: UploadResponse;
};

function ratio(numerator: number, denominator: number): string {
  if (denominator <= 0) return "0%";
  return `${Math.round((numerator / denominator) * 100)}%`;
}

export default function SummaryCards({ result }: SummaryCardsProps) {
  const { summary } = result;

  const cards = [
    { label: "Total Events", value: summary.total_events.toString(), hint: "Parsed rows saved" },
    {
      label: "Blocked Events",
      value: summary.blocked_events.toString(),
      hint: ratio(summary.blocked_events, summary.total_events)
    },
    {
      label: "Anomalies",
      value: summary.total_anomalies.toString(),
      hint: `${result.anomalies_detected} detected in upload`
    },
    { label: "Unique Source IPs", value: summary.unique_ips.toString(), hint: "Distinct senders" },
    {
      label: "Parse Errors",
      value: result.parse_errors_count.toString(),
      hint: result.parse_errors_count > 0 ? "Needs review" : "Clean parse"
    }
  ];

  return (
    <section className="analysis-grid">
      {cards.map((card) => (
        <article key={card.label} className="analysis-card">
          <h3>{card.label}</h3>
          <p className="analysis-value">{card.value}</p>
          <small>{card.hint}</small>
        </article>
      ))}
    </section>
  );
}
