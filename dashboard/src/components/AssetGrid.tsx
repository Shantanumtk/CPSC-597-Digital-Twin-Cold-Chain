'use client';

import { Truck, Warehouse, Thermometer, Droplets, DoorOpen } from 'lucide-react';
import { Asset } from '@/types';

interface AssetGridProps {
  assets: Asset[];
  onSelectAsset: (asset: Asset) => void;
  selectedAssetId?: string;
  convertTemp?: (celsius: number | undefined) => string;
}

const stateColors = {
  NORMAL: 'border-green-500 bg-green-50',
  WARNING: 'border-yellow-500 bg-yellow-50',
  CRITICAL: 'border-red-500 bg-red-50',
};

const stateBadgeColors = {
  NORMAL: 'bg-green-500',
  WARNING: 'bg-yellow-500',
  CRITICAL: 'bg-red-500',
};

export default function AssetGrid({
  assets,
  onSelectAsset,
  selectedAssetId,
  convertTemp = (c) => (c !== undefined ? `${c.toFixed(1)}°C` : '--'),
}: AssetGridProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">Assets ({assets.length})</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto">
        {assets.map((asset) => (
          <div
            key={asset.asset_id}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              stateColors[asset.state]
            } ${
              selectedAssetId === asset.asset_id
                ? 'ring-2 ring-blue-500'
                : 'hover:shadow-md'
            }`}
            onClick={() => onSelectAsset(asset)}
          >
            {/* Header Row */}
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                {asset.asset_type === 'refrigerated_truck' ? (
                  <Truck className="w-5 h-5 text-gray-600 flex-shrink-0" />
                ) : (
                  <Warehouse className="w-5 h-5 text-gray-600 flex-shrink-0" />
                )}
                <span className="font-medium text-sm truncate">{asset.asset_id}</span>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs text-white font-medium flex-shrink-0 ${
                  stateBadgeColors[asset.state]
                }`}
              >
                {asset.state}
              </span>
            </div>

            {/* Metrics */}
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <span className="font-medium">{convertTemp(asset.temperature_c)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Droplets className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <span>{asset.humidity_pct?.toFixed(1)}%</span>
              </div>
              {asset.door_open && (
                <div className="flex items-center gap-2 text-orange-600">
                  <DoorOpen className="w-4 h-4 flex-shrink-0" />
                  <span className="font-medium">Door Open</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}