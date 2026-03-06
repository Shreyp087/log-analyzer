import type { UploadEventPreview } from "@/types";

type TimelineTableProps = {
  events: UploadEventPreview[];
};

function formatTime(value: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export default function TimelineTable({ events }: TimelineTableProps) {
  return (
    <section className="analysis-section">
      <div className="section-head">
        <h2>Event Timeline</h2>
        <span>{events.length} rows</span>
      </div>

      {events.length === 0 ? (
        <p className="muted">No event preview rows available for this analysis.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Source IP</th>
                <th>Action</th>
                <th>Category</th>
                <th>Destination</th>
                <th>Bytes</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, index) => (
                <tr key={`${event.event_time || "row"}-${index}`}>
                  <td>{formatTime(event.event_time)}</td>
                  <td>{event.username || "-"}</td>
                  <td>{event.source_ip || "-"}</td>
                  <td>{event.action || "-"}</td>
                  <td>{event.category || "-"}</td>
                  <td className="truncate">{event.destination || "-"}</td>
                  <td>{event.bytes_transferred ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
