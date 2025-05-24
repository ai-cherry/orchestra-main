import React from "react";
import {
  Area,
  AreaChart as RechartsAreaChart,
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "../../lib/utils";

/**
 * Props for the LineChart component
 */
interface LineChartProps {
  data: any[];
  xAxisKey: string;
  yAxisKey: string;
  className?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  lineColor?: string;
}

/**
 * Line chart component
 */
export const LineChart = ({
  data,
  xAxisKey,
  yAxisKey,
  className,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  lineColor = "var(--primary)",
}: LineChartProps) => {
  return (
    <div className={cn("w-full h-full", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart
          data={data}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" opacity={0.2} />}
          <XAxis
            dataKey={xAxisKey}
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--popover)",
                borderColor: "var(--border)",
                color: "var(--popover-foreground)",
                fontSize: "12px",
                borderRadius: "6px",
              }}
            />
          )}
          {showLegend && <Legend />}
          <Line
            type="monotone"
            dataKey={yAxisKey}
            stroke={lineColor}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Props for the AreaChart component
 */
interface AreaChartProps {
  data: any[];
  categories: string[];
  colors?: string[];
  xAxisKey: string;
  className?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  stackOffset?: "none" | "expand" | "wiggle" | "silhouette";
}

/**
 * Area chart component
 */
export const AreaChart = ({
  data,
  categories,
  colors = ["var(--primary)", "var(--secondary)", "var(--accent)"],
  xAxisKey,
  className,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  stackOffset = "none",
}: AreaChartProps) => {
  return (
    <div className={cn("w-full h-full", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsAreaChart
          data={data}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          stackOffset={stackOffset}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" opacity={0.2} />}
          <XAxis
            dataKey={xAxisKey}
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--popover)",
                borderColor: "var(--border)",
                color: "var(--popover-foreground)",
                fontSize: "12px",
                borderRadius: "6px",
              }}
            />
          )}
          {showLegend && <Legend />}
          {categories.map((category, index) => (
            <Area
              key={category}
              type="monotone"
              dataKey={category}
              stackId="1"
              stroke={colors[index % colors.length]}
              fill={colors[index % colors.length]}
              fillOpacity={0.6}
            />
          ))}
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Props for the BarChart component
 */
interface BarChartProps {
  data: any[];
  xAxisKey: string;
  yAxisKey: string;
  className?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  barColor?: string;
}

/**
 * Bar chart component
 */
export const BarChart = ({
  data,
  xAxisKey,
  yAxisKey,
  className,
  showGrid = true,
  showLegend = false,
  showTooltip = true,
  barColor = "var(--primary)",
}: BarChartProps) => {
  return (
    <div className={cn("w-full h-full", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" opacity={0.2} />}
          <XAxis
            dataKey={xAxisKey}
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="var(--muted-foreground)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--popover)",
                borderColor: "var(--border)",
                color: "var(--popover-foreground)",
                fontSize: "12px",
                borderRadius: "6px",
              }}
            />
          )}
          {showLegend && <Legend />}
          <Bar dataKey={yAxisKey} fill={barColor} radius={[4, 4, 0, 0]} />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
};
