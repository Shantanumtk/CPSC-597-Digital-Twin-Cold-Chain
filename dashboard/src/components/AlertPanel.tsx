'use client';

import { AlertTriangle, Clock } from 'lucide-react';
import { Alert } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface AlertPanelProps {
  alerts: Alert[];
  onSelectAsset: (assetId: string) => void;
}

const stateColors = {
  WARNING: 'border-yellow-500 bg-yellow-50',
  CRITICAL: 'border-red-500 bg-red-50',
};

export default function AlertPanel({ alerts, onSelectAsset }: AlertPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-orange-500" />
        <h2 className="text-lg font-semibold">Active Alerts ({alerts.length})</h2>
      </div>

      {alerts.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No active alerts</p>
      ) : (
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {alerts.map((alert, index) => (
            <div
              key={`${alert.asset_id}-${index}`}
              className={`border-l-4 rounded-r-lg p-3 cursor-pointer hover:shadow-md transition-shadow ${
                stateColors[alert.state as keyof typeof stateColors] || 'border-gray-500 bg-gray-50'
              }`}
              onClick={() => onSelectAsset(alert.asset_id)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{alert.asset_id}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs text-white ${
                    alert.state === 'CRITICAL' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}
                >
                  {alert.state}
                </span>
              </div>

              {alert.reasons?.map((reason, i) => (
                <p key={i} className="text-sm text-gray-600">
                  {reason}
                </p>
              ))}

              {alert.created_at && (
                <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                  <Clock className="w-3 h-3" />
                  <span>
                    {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}