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
  const hourlyData = useMemo(() => {
    const hours = Array.from({ length: 24 }, (_, hour) => ({ hour, count: 0 }));
    for (const event of events) {
      const timestamp = eventTimestamp(event);
      if (!timestamp) continue;
      const parsed = new Date(timestamp);
      if (Number.isNaN(parsed.getTime())) continue;
      const hour = parsed.getUTCHours();
      if (hour >= 0 && hour <= 23) {
        hours[hour].count += 1;
      }
    }
    return hours;
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
        <h3>Event Volume by Hour</h3>
        <div className="chart-body">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="hourlyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1b3442" />
              <XAxis dataKey="hour" stroke="#9dc3d8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#9dc3d8" tick={{ fontSize: 11 }} />
              <Tooltip />
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
