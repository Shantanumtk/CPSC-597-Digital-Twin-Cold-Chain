'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchStats, fetchAssets, fetchActiveAlerts } from '@/lib/api';
import { Stats, Asset, Alert } from '@/types';

export function useApi(refreshInterval: number = 5000) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [statsData, assetsData, alertsData] = await Promise.all([
        fetchStats(),
        fetchAssets(),
        fetchActiveAlerts(),
      ]);
      
      setStats(statsData);
      setAssets(assetsData);
      setAlerts(alertsData.alerts || []);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { stats, assets, alerts, loading, error, lastUpdated, refresh };
}