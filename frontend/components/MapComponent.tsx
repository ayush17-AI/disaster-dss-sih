"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function MapComponent() {
  const [zones, setZones] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/zones?region=Wayanad&rainfall_intensity=50&construction_load=1.0")
      .then(res => res.json())
      .then(data => setZones(data))
      .catch(err => console.error("Error fetching zones:", err));
  }, []);

  const getStyle = (feature: any) => {
    return {
      fillColor: feature.properties.zone_color === "RED" ? "#ef4444" : "#eab308",
      weight: 2,
      opacity: 0.8,
      color: feature.properties.zone_color === "RED" ? "#b91c1c" : "#ca8a04",
      dashArray: '4',
      fillOpacity: 0.4
    };
  };

  return (
    <MapContainer center={[11.545, 76.145]} zoom={13} style={{ height: "100%", width: "100%", background: "#111827" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      {zones && <GeoJSON data={zones} style={getStyle} />}
    </MapContainer>
  );
}
