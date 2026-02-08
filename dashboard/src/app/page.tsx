'use client';

import { useState } from 'react';
import { useApi } from '@/hooks/useApi';
import Header from '@/components/Header';
import StatsCards from '@/components/StatsCards';
import AssetGrid from '@/components/AssetGrid';
import AssetMap from '@/components/AssetMap';
import AlertPanel from '@/components/AlertPanel';
import AssetDetail from '@/components/AssetDetail';
import { Asset } from '@/types';

export default function Dashboard() {
  const { stats, assets, alerts, loading, error, lastUpdated } = useApi(5000);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [activeView, setActiveView] = useState<string>('dashboard');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const filteredAssets = assets.filter((asset) => {
    if (stateFilter && asset.state !== stateFilter) return false;
    if (typeFilter && asset.asset_type !== typeFilter) return false;
    return true;
  });

  const trucks = assets.filter((a) => a.asset_type === 'refrigerated_truck');

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  const handleSelectAssetById = (id: string) => {
    const asset = assets.find((a) => a.asset_id === id);
    if (asset) setSelectedAsset(asset);
  };

  // Render different views based on activeView
  const renderContent = () => {
    switch (activeView) {
      case 'map':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AssetMap
                trucks={trucks}
                onSelectAsset={setSelectedAsset}
                selectedAssetId={selectedAsset?.asset_id}
              />
            </div>
            <div>
              {selectedAsset ? (
                <AssetDetail
                  asset={selectedAsset}
                  onClose={() => setSelectedAsset(null)}
                />
              ) : (
                <AlertPanel
                  alerts={alerts}
                  onSelectAsset={handleSelectAssetById}
                />
              )}
            </div>
          </div>
        );

      case 'alerts':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">Active Alerts ({alerts.length})</h2>
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {alerts.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No active alerts 🎉</p>
                ) : (
                  alerts.map((alert, index) => (
                    <div
                      key={`${alert.asset_id}-${index}`}
                      className={`border-l-4 rounded-r-lg p-4 cursor-pointer hover:shadow-md ${
                        alert.state === 'CRITICAL'
                          ? 'border-red-500 bg-red-50'
                          : 'border-yellow-500 bg-yellow-50'
                      }`}
                      onClick={() => handleSelectAssetById(alert.asset_id)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold">{alert.asset_id}</p>
                          {alert.reasons?.map((reason, i) => (
                            <p key={i} className="text-sm text-gray-600 mt-1">{reason}</p>
                          ))}
                        </div>
                        <span
                          className={`px-2 py-1 rounded text-xs text-white ${
                            alert.state === 'CRITICAL' ? 'bg-red-500' : 'bg-yellow-500'
                          }`}
                        >
                          {alert.state}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div>
              {selectedAsset && (
                <AssetDetail
                  asset={selectedAsset}
                  onClose={() => setSelectedAsset(null)}
                />
              )}
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics</h2>
            <p className="text-gray-600">Coming soon in Phase 7</p>
          </div>
        );

      case 'settings':
        return (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-6xl mb-4">⚙️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Settings</h2>
            <p className="text-gray-600">Coming soon</p>
          </div>
        );

      default: // dashboard
        return (
          <>
            {/* Stats Cards */}
            {stats && <StatsCards stats={stats} />}

            {/* Filters */}
            <div className="flex flex-wrap gap-4 items-center">
              <select
                className="px-4 py-2 border rounded-lg bg-white"
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
              >
                <option value="">All States</option>
                <option value="NORMAL">Normal</option>
                <option value="WARNING">Warning</option>
                <option value="CRITICAL">Critical</option>
              </select>

              <select
                className="px-4 py-2 border rounded-lg bg-white"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="refrigerated_truck">Trucks</option>
                <option value="cold_room">Cold Rooms</option>
              </select>

              <span className="text-sm text-gray-500">
                Showing {filteredAssets.length} of {assets.length} assets
              </span>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <AssetGrid
                  assets={filteredAssets}
                  onSelectAsset={setSelectedAsset}
                  selectedAssetId={selectedAsset?.asset_id}
                />
              </div>
              <div>
                {selectedAsset ? (
                  <AssetDetail
                    asset={selectedAsset}
                    onClose={() => setSelectedAsset(null)}
                  />
                ) : (
                  <AlertPanel
                    alerts={alerts}
                    onSelectAsset={handleSelectAssetById}
                  />
                )}
              </div>
            </div>
          </>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header
        lastUpdated={lastUpdated}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {renderContent()}
      </main>
    </div>
  );
}