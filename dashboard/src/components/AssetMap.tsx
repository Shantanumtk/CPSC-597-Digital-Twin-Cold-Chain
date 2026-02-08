'use client';

import { useEffect, useState } from 'react';
import { Asset } from '@/types';
import dynamic from 'next/dynamic';

interface AssetMapProps {
  trucks: Asset[];
  onSelectAsset: (asset: Asset) => void;
  selectedAssetId?: string;
}

// Dynamically import map to avoid SSR issues
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
);
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
);

export default function AssetMap({
  trucks,
  onSelectAsset,
  selectedAssetId,
}: AssetMapProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="bg-white rounded-lg shadow p-4 h-[500px] flex items-center justify-center">
        Loading map...
      </div>
    );
  }

  // Filter trucks with valid locations
  const trucksWithLocation = trucks.filter(
    (t) => t.location?.latitude && t.location?.longitude
  );

  // Default center (Los Angeles area)
  const center: [number, number] = trucksWithLocation.length > 0
    ? [trucksWithLocation[0].location!.latitude, trucksWithLocation[0].location!.longitude]
    : [34.0522, -118.2437];

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">
        Live Truck Locations ({trucksWithLocation.length})
      </h2>
      
      <div className="h-[500px] rounded-lg overflow-hidden">
        <MapContainer
          center={center}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {trucksWithLocation.map((truck) => (
            <Marker
              key={truck.asset_id}
              position={[truck.location!.latitude, truck.location!.longitude]}
              eventHandlers={{
                click: () => onSelectAsset(truck),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{truck.asset_id}</p>
                  <p>Temp: {truck.temperature_c?.toFixed(1)}°C</p>
                  <p>State: {truck.state}</p>
                  {truck.location?.speed_kmh && (
                    <p>Speed: {truck.location.speed_kmh.toFixed(1)} km/h</p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}