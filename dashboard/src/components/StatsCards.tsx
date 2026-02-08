'use client';

import { Truck, Warehouse, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { Stats } from '@/types';

interface StatsCardsProps {
  stats: Stats;
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Total Assets',
      value: stats.total_assets,
      icon: <Warehouse className="w-6 h-6" />,
      color: 'bg-blue-500',
    },
    {
      title: 'Trucks',
      value: stats.asset_types.refrigerated_truck,
      icon: <Truck className="w-6 h-6" />,
      color: 'bg-indigo-500',
    },
    {
      title: 'Normal',
      value: stats.state_counts.NORMAL,
      icon: <CheckCircle className="w-6 h-6" />,
      color: 'bg-green-500',
    },
    {
      title: 'Warning',
      value: stats.state_counts.WARNING,
      icon: <AlertTriangle className="w-6 h-6" />,
      color: 'bg-yellow-500',
    },
    {
      title: 'Critical',
      value: stats.state_counts.CRITICAL,
      icon: <XCircle className="w-6 h-6" />,
      color: 'bg-red-500',
    },
    {
      title: 'Active Alerts',
      value: stats.active_alerts,
      icon: <AlertTriangle className="w-6 h-6" />,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-lg shadow p-4 flex items-center gap-4"
        >
          <div className={`${card.color} text-white p-3 rounded-lg`}>
            {card.icon}
          </div>
          <div>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className="text-sm text-gray-500">{card.title}</p>
          </div>
        </div>
      ))}
    </div>
  );
}