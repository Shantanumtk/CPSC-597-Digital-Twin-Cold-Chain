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
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm text-gray-500 mb-1">Avg Temperature (Trucks)</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {trucks.length > 0
                    ? (trucks.reduce((sum, t) => sum + (t.temperature_c || 0), 0) / trucks.length).toFixed(1)
                    : '--'}°C
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm text-gray-500 mb-1">Avg Temperature (Rooms)</h3>
                <p className="text-2xl font-bold text-cyan-600">
                  {assets.filter(a => a.asset_type === 'cold_room').length > 0
                    ? (assets.filter(a => a.asset_type === 'cold_room').reduce((sum, t) => sum + (t.temperature_c || 0), 0) / assets.filter(a => a.asset_type === 'cold_room').length).toFixed(1)
                    : '--'}°C
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm text-gray-500 mb-1">Doors Open</h3>
                <p className="text-2xl font-bold text-orange-600">
                  {assets.filter(a => a.door_open).length}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm text-gray-500 mb-1">Compressors Off</h3>
                <p className="text-2xl font-bold text-red-600">
                  {assets.filter(a => !a.compressor_running).length}
                </p>
              </div>
            </div>

            {/* State Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">State Distribution</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Normal</span>
                      <span className="text-sm font-medium">{stats?.state_counts.NORMAL || 0}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-green-500 h-4 rounded-full transition-all"
                        style={{ width: `${stats ? (stats.state_counts.NORMAL / stats.total_assets) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Warning</span>
                      <span className="text-sm font-medium">{stats?.state_counts.WARNING || 0}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-yellow-500 h-4 rounded-full transition-all"
                        style={{ width: `${stats ? (stats.state_counts.WARNING / stats.total_assets) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Critical</span>
                      <span className="text-sm font-medium">{stats?.state_counts.CRITICAL || 0}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-red-500 h-4 rounded-full transition-all"
                        style={{ width: `${stats ? (stats.state_counts.CRITICAL / stats.total_assets) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Asset Types</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Refrigerated Trucks</span>
                      <span className="text-sm font-medium">{stats?.asset_types.refrigerated_truck || 0}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-indigo-500 h-4 rounded-full transition-all"
                        style={{ width: `${stats ? (stats.asset_types.refrigerated_truck / stats.total_assets) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600">Cold Rooms</span>
                      <span className="text-sm font-medium">{stats?.asset_types.cold_room || 0}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-500 h-4 rounded-full transition-all"
                        style={{ width: `${stats ? (stats.asset_types.cold_room / stats.total_assets) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Temperature Overview Table */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Temperature Overview</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">Asset</th>
                      <th className="text-left py-2 px-4">Type</th>
                      <th className="text-left py-2 px-4">Temperature</th>
                      <th className="text-left py-2 px-4">Humidity</th>
                      <th className="text-left py-2 px-4">State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assets.slice(0, 10).map((asset) => (
                      <tr key={asset.asset_id} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4 font-medium">{asset.asset_id}</td>
                        <td className="py-2 px-4 text-gray-600">
                          {asset.asset_type === 'refrigerated_truck' ? 'Truck' : 'Room'}
                        </td>
                        <td className="py-2 px-4">{asset.temperature_c?.toFixed(1)}°C</td>
                        <td className="py-2 px-4">{asset.humidity_pct?.toFixed(1)}%</td>
                        <td className="py-2 px-4">
                          <span
                            className={`px-2 py-1 rounded text-xs text-white ${
                              asset.state === 'NORMAL'
                                ? 'bg-green-500'
                                : asset.state === 'WARNING'
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                          >
                            {asset.state}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Dashboard Settings</h3>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Auto-refresh Interval
                  </label>
                  <select className="w-full md:w-64 px-4 py-2 border rounded-lg bg-white">
                    <option value="3000">3 seconds</option>
                    <option value="5000">5 seconds (default)</option>
                    <option value="10000">10 seconds</option>
                    <option value="30000">30 seconds</option>
                    <option value="60000">1 minute</option>
                  </select>
                  <p className="text-sm text-gray-500 mt-1">How often the dashboard fetches new data</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature Unit
                  </label>
                  <select className="w-full md:w-64 px-4 py-2 border rounded-lg bg-white">
                    <option value="celsius">Celsius (°C)</option>
                    <option value="fahrenheit">Fahrenheit (°F)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Temperature Thresholds</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Refrigerated Trucks</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Warning Above</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          defaultValue="-10"
                          className="w-24 px-3 py-2 border rounded-lg"
                        />
                        <span className="text-gray-500">°C</span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Critical Above</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          defaultValue="-5"
                          className="w-24 px-3 py-2 border rounded-lg"
                        />
                        <span className="text-gray-500">°C</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Cold Rooms</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Warning Above</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          defaultValue="-15"
                          className="w-24 px-3 py-2 border rounded-lg"
                        />
                        <span className="text-gray-500">°C</span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Critical Above</label>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          defaultValue="-10"
                          className="w-24 px-3 py-2 border rounded-lg"
                        />
                        <span className="text-gray-500">°C</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">System Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">API Endpoint</span>
                  <span className="font-mono text-gray-800">/api (proxy)</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Total Assets</span>
                  <span className="font-medium">{stats?.total_assets || 0}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Active Alerts</span>
                  <span className="font-medium">{stats?.active_alerts || 0}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Last Updated</span>
                  <span className="font-medium">{lastUpdated?.toLocaleTimeString() || '--'}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Save Settings
              </button>
            </div>
          </div>
        );

      default:
        return (
          <>
            {stats && <StatsCards stats={stats} />}

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