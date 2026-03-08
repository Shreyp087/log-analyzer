"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { CATEGORY_BAR_COLORS } from "@/lib/constants";
import type { UploadEventPreview, UploadSummaryPayload } from "@/types";

type AnalysisChartsProps = {
  events: UploadEventPreview[];
  summary: UploadSummaryPayload;
};

function eventAction(event: UploadEventPreview): string {
  return (event.action || "").toUpperCase();
}

function eventCategory(event: UploadEventPreview): string {
  return (event.category || "Unknown").trim() || "Unknown";
}

function eventTimestamp(event: UploadEventPreview): string | null {
  return event.event_time || null;
}

export default function AnalysisCharts({ events, summary }: AnalysisChartsProps) {
  const timelineData = useMemo(() => {
    const parsedTimes = events
      .map((event) => eventTimestamp(event))
      .filter((timestamp): timestamp is string => Boolean(timestamp))
      .map((timestamp) => new Date(timestamp))
      .filter((date) => !Number.isNaN(date.getTime()))
      .map((date) => date.getTime())
      .sort((a, b) => a - b);

    if (parsedTimes.length === 0) {
      return [] as Array<{ timestampMs: number; count: number }>;
    }

    const first = parsedTimes[0];
    const last = parsedTimes[parsedTimes.length - 1];
    const spanMs = Math.max(last - first, 1);

    let bucketMs = 5 * 60 * 1000; // 5 minutes
    if (spanMs > 2 * 60 * 60 * 1000) bucketMs = 30 * 60 * 1000; // 30 minutes
    if (spanMs > 24 * 60 * 60 * 1000) bucketMs = 2 * 60 * 60 * 1000; // 2 hours
    if (spanMs > 7 * 24 * 60 * 60 * 1000) bucketMs = 24 * 60 * 60 * 1000; // 1 day

    const bucketedCounts = new Map<number, number>();
    for (const timeMs of parsedTimes) {
      const bucketStart = Math.floor(timeMs / bucketMs) * bucketMs;
      bucketedCounts.set(bucketStart, (bucketedCounts.get(bucketStart) || 0) + 1);
    }

    return [...bucketedCounts.entries()]
      .sort((a, b) => a[0] - b[0])
      .map(([timestampMs, count]) => ({ timestampMs, count }));
  }, [events]);

  const actionData = useMemo(() => {
    let allow = 0;
    let block = 0;
    let permit = 0;
    let other = 0;

    for (const event of events) {
      const action = eventAction(event);
      if (action === "ALLOW") {
        allow += 1;
      } else if (action === "PERMIT") {
        permit += 1;
      } else if (action === "BLOCK") {
        block += 1;
      } else {
        other += 1;
      }
    }

    return [
      { name: "ALLOW", value: allow, color: "#00ff88" },
      { name: "BLOCK", value: block, color: "#ff4444" },
      { name: "PERMIT", value: permit, color: "#00d4ff" },
      { name: "OTHER", value: other, color: "#6f86a2" }
    ];
  }, [events]);

  const categoryData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const event of events) {
      const category = eventCategory(event);
      counts.set(category, (counts.get(category) || 0) + 1);
    }

    const fromEvents = [...counts.entries()]
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);

    if (fromEvents.length > 0) {
      return fromEvents;
    }

    return (summary.top_categories || []).map((item) => ({
      category: item.value,
      count: item.count,
    }));
  }, [events, summary.top_categories]);

  return (
    <section className="analytics-grid">
      <article className="chart-card">
        <h3>Event Volume Over Time</h3>
        <div className="chart-body">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={timelineData}>
              <defs>
                <linearGradient id="hourlyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b3442" />
              <XAxis
                type="number"
                dataKey="timestampMs"
                domain={["dataMin", "dataMax"]}
                stroke="#9dc3d8"
                tick={{ fontSize: 11 }}
                tickFormatter={(value) =>
                  new Date(Number(value)).toLocaleString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                  })
                }
              />
              <YAxis stroke="#9dc3d8" tick={{ fontSize: 11 }} />
              <Tooltip
                labelFormatter={(value) =>
                  new Date(Number(value)).toLocaleString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                }
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#00d4ff"
                strokeWidth={2}
                fill="url(#hourlyGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="chart-card">
        <h3>Action Distribution</h3>
        <div className="chart-body">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={actionData}
                dataKey="value"
                nameKey="name"
                innerRadius={52}
                outerRadius={88}
                label={(entry) => `${entry.name}: ${entry.value}`}
              >
                {actionData.map((slice) => (
                  <Cell key={slice.name} fill={slice.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="chart-card chart-card-wide">
        <h3>Events by Category</h3>
        <div className="chart-body">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={categoryData} layout="vertical" margin={{ left: 20, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b3442" />
              <XAxis type="number" stroke="#9dc3d8" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="category" stroke="#9dc3d8" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                {categoryData.map((row, index) => (
                  <Cell
                    key={`${row.category}-${row.count}`}
                    fill={CATEGORY_BAR_COLORS[index % CATEGORY_BAR_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>
    </section>
  );
}
