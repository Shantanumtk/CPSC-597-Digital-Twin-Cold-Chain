'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { format } from 'date-fns';
import { TelemetryPoint } from '@/types';

interface TemperatureChartProps {
  data: TelemetryPoint[];
}

export default function TemperatureChart({ data }: TemperatureChartProps) {
  // Reverse to show oldest first
  const chartData = [...data].reverse().map((point) => ({
    time: format(new Date(point.created_at), 'HH:mm'),
    temperature: point.temperature_c,
    humidity: point.humidity_pct,
  }));

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10 }}
            domain={['auto', 'auto']}
            tickFormatter={(v) => `${v}°`}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              name === 'temperature' ? `${value.toFixed(1)}°C` : `${value.toFixed(1)}%`,
              name === 'temperature' ? 'Temp' : 'Humidity',
            ]}
          />
          <ReferenceLine y={-10} stroke="#ef4444" strokeDasharray="5 5" />
          <ReferenceLine y={-18} stroke="#22c55e" strokeDasharray="5 5" />
          <Line
            type="monotone"
            dataKey="temperature"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}