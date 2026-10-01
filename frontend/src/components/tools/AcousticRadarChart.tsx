import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import { AudioFeatures } from '../../types/assessment';

interface AcousticRadarChartProps {
  features?: AudioFeatures | null;
}

export const AcousticRadarChart: React.FC<AcousticRadarChartProps> = ({ features }) => {
  if (!features) {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-center text-gray-500 text-sm">
        <p>No acoustic recording provided for this session.</p>
        <p className="text-xs text-gray-600 mt-1">Audio was skipped or omitted during screening.</p>
      </div>
    );
  }

  // Map 0-1 values to percentages 0-100 for clear visualization
  // Normative reference baseline reflects healthy conversational speech norms (Cummins et al. 2015)
  const data = [
    {
      metric: 'Loudness (RMS)',
      user: Math.round(features.rms_mean * 100),
      healthy: 45,
      fullMark: 100,
    },
    {
      metric: 'Dynamics (RMS σ)',
      user: Math.round(Math.min(1.0, features.rms_std / 0.25) * 100),
      healthy: 65,
      fullMark: 100,
    },
    {
      metric: 'Voicing Rate (ZCR)',
      user: Math.round(features.zcr_mean * 100),
      healthy: 30,
      fullMark: 100,
    },
    {
      metric: 'Brightness (Centroid)',
      user: Math.round(features.spectral_centroid * 100),
      healthy: 55,
      fullMark: 100,
    },
    {
      metric: 'High Freq (Rolloff)',
      user: Math.round(features.spectral_rolloff * 100),
      healthy: 60,
      fullMark: 100,
    },
    {
      metric: 'Continuity (Speaking)',
      user: Math.round(features.speaking_ratio * 100),
      healthy: 80,
      fullMark: 100,
    },
  ];

  return (
    <div className="w-full flex flex-col items-center">
      <div className="h-[280px] w-full max-w-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="rgba(255, 255, 255, 0.15)" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: '#94D2BD', fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fill: '#6b7280', fontSize: 10 }}
            />
            <Radar
              name="Healthy Baseline"
              dataKey="healthy"
              stroke="#E9C46A"
              fill="#E9C46A"
              fillOpacity={0.15}
              strokeDasharray="4 4"
            />
            <Radar
              name="User Acoustic Footprint"
              dataKey="user"
              stroke="#0A9396"
              fill="#0A9396"
              fillOpacity={0.45}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0D1B2A',
                borderColor: 'rgba(255,255,255,0.15)',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#fff',
              }}
              formatter={(val: number) => [`${val}%`, '']}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center max-w-sm">
        Acoustic somatic profile: Lower values across dynamics and loudness indicate flat, monotone affect.
      </p>
    </div>
  );
};
