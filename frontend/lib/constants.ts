export const CATEGORY_BAR_COLORS = [
  "#00d4ff",
  "#00ff88",
  "#ffb800",
  "#ff8800",
  "#aa66ff",
  "#ff4444",
] as const;

export const SEVERITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export const RISK_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const;

export type RiskLevel = (typeof RISK_LEVELS)[number];
