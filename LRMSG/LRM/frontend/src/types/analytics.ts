export interface HistoricalKPIs {
  total_events: number;
  peak_year: number;
  peak_month: string;
  top_state: string;
  recurring_hotspots: number;
}

export interface YearlyTrend {
  year: number;
  count: number;
}

export interface MonthlyPattern {
  month: string;
  count: number;
}

export interface StateDistribution {
  state: string;
  count: number;
}

export interface HeatmapData {
  state: string;
  years: { [year: string]: number };
}

export interface Hotspot {
  state: string;
  district: string;
  total_events: number;
  active_years: number;
  avg_rainfall?: number;
  avg_slope?: number;
  avg_elevation?: number;
  common_season?: string;
}

export interface HistoricalEvent {
  latitude: number;
  longitude: number;
  year: number;
  month_name: string;
  state: string;
  district: string;
  event_date: string;
}

export interface CorrelationData {
  factor_x: string;
  factor_y: string;
  value: number;
}

export interface CalendarData {
  date: string;
  count: number;
}

export interface HistoricalAnalyticsResponse {
  kpis: HistoricalKPIs;
  yearly_trend: YearlyTrend[];
  monthly_pattern: MonthlyPattern[];
  state_distribution: StateDistribution[];
  heatmap: HeatmapData[];
  hotspots: Hotspot[];
  events: HistoricalEvent[];
  available_states: string[];
  correlation_matrix?: CorrelationData[];
  calendar_heatmap?: CalendarData[];
}
