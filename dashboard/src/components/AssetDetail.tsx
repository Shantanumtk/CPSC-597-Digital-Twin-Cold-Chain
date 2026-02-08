'use client';

import { useState, useEffect } from 'react';
import {
  X,
  Thermometer,
  Droplets,
  DoorOpen,
  Power,
  MapPin,
  Gauge,
  History,
} from 'lucide-react';
import { Asset, AssetHistory } from '@/types';
import { fetchAssetHistory } from '@/lib/api';
import TemperatureChart from './TemperatureChart';

interface AssetDetailProps {
  asset: Asset;
  onClose: () => void;
}

export default function AssetDetail({ asset, onClose }: AssetDetailProps) {
  const [history, setHistory] = useState<AssetHistory | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    async function loadHistory() {
      setLoadingHistory(true);
      try {
        const data = await fetchAssetHistory(asset.asset_id, 6);
        setHistory(data);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoadingHistory(false);
      }
    }
    loadHistory();
  }, [asset.asset_id]);

  const stateColors = {
    NORMAL: 'bg-green-500',
    WARNING: 'bg-yellow-500',
    CRITICAL: 'bg-red-500',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{asset.asset_id}</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* State Badge */}
      <div className="mb-4">
        <span
          className={`px-3 py-1 rounded-full text-white text-sm ${
            stateColors[asset.state]
          }`}
        >
          {asset.state}
        </span>
        <span className="ml-2 text-sm text-gray-500">
          {asset.asset_type === 'refrigerated_truck' ? 'Truck' : 'Cold Room'}
        </span>
      </div>

      {/* Reasons */}
      {asset.reasons?.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-800 mb-1">Issues:</p>
          {asset.reasons.map((reason, i) => (
            <p key={i} className="text-sm text-red-700">
              • {reason}
            </p>
          ))}
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <Thermometer className="w-5 h-5 text-blue-500" />
          <div>
            <p className="text-lg font-bold">{asset.temperature_c?.toFixed(1)}°C</p>
            <p className="text-xs text-gray-500">Temperature</p>
          </div>
        </div>

        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <Droplets className="w-5 h-5 text-cyan-500" />
          <div>
            <p className="text-lg font-bold">{asset.humidity_pct?.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">Humidity</p>
          </div>
        </div>

        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <DoorOpen
            className={`w-5 h-5 ${
              asset.door_open ? 'text-orange-500' : 'text-gray-400'
            }`}
          />
          <div>
            <p className="text-lg font-bold">
              {asset.door_open ? 'Open' : 'Closed'}
            </p>
            <p className="text-xs text-gray-500">Door</p>
          </div>
        </div>

        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <Power
            className={`w-5 h-5 ${
              asset.compressor_running ? 'text-green-500' : 'text-gray-400'
            }`}
          />
          <div>
            <p className="text-lg font-bold">
              {asset.compressor_running ? 'Running' : 'Off'}
            </p>
            <p className="text-xs text-gray-500">Compressor</p>
          </div>
        </div>
      </div>

      {/* Location (for trucks) */}
      {asset.location && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium">Location</span>
          </div>
          <p className="text-sm text-gray-600">
            {asset.location.latitude.toFixed(4)}, {asset.location.longitude.toFixed(4)}
          </p>
          {asset.location.speed_kmh !== undefined && (
            <div className="flex items-center gap-1 mt-1">
              <Gauge className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                {asset.location.speed_kmh.toFixed(1)} km/h
              </span>
            </div>
          )}
        </div>
      )}

      {/* Temperature History Chart */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <History className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium">Temperature History (6h)</span>
        </div>
        
        {loadingHistory ? (
          <div className="h-48 flex items-center justify-center text-gray-400">
            Loading...
          </div>
        ) : history && history.telemetry.length > 0 ? (
          <TemperatureChart data={history.telemetry} />
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-400">
            No history available
          </div>
        )}
      </div>
    </div>
  );
}
