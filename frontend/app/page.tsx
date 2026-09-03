"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const MapComponent = dynamic(() => import("../components/MapComponent"), { ssr: false });

export default function Dashboard() {
  const [triageData, setTriageData] = useState([]);
  
  useEffect(() => {
    fetch("http://localhost:8000/api/triage?region=Wayanad")
      .then(res => res.json())
      .then(data => setTriageData(data))
      .catch(err => console.error("Error fetching triage data:", err));
  }, []);

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 p-4 flex flex-col gap-4 z-10 shadow-lg border-r border-gray-700">
        <h1 className="text-xl font-bold mb-4 text-blue-400">Disaster DSS</h1>
        <div>
          <h2 className="text-sm text-gray-400 uppercase font-semibold mb-2">Layers</h2>
          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" defaultChecked className="accent-blue-500" /> Hazard Zones</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="accent-blue-500" /> Slope Gradient</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="accent-blue-500" /> Live Rainfall</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="accent-blue-500" /> Built Footprint</label>
          </div>
        </div>
        <div className="mt-auto pb-4">
          <h2 className="text-sm text-gray-400 uppercase font-semibold mb-2">Simulation</h2>
          <div className="flex flex-col gap-4">
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs">Rainfall Intensity</label>
                <span className="text-xs text-gray-400">50 mm/hr</span>
              </div>
              <input type="range" min="0" max="150" defaultValue="50" className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs">Const. Surcharge</label>
                <span className="text-xs text-gray-400">1.0x</span>
              </div>
              <input type="range" min="1.0" max="2.5" step="0.1" defaultValue="1.0" className="w-full accent-blue-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <div className="absolute top-4 left-4 z-[1000]">
          <span className="bg-red-600/90 backdrop-blur text-white px-3 py-1.5 rounded-full text-xs font-bold shadow border border-red-500">
            MODE: MOUNTAIN_CASCADE
          </span>
        </div>
        
        {/* Map Canvas */}
        <div className="flex-1 bg-gray-900 relative">
          <MapComponent />
        </div>
      </div>

      {/* Right Slide-over Panel (Triage Manifest) */}
      <div className="w-80 bg-gray-800 p-4 border-l border-gray-700 flex flex-col z-10 shadow-lg overflow-y-auto">
        <h2 className="text-lg font-bold mb-4 text-orange-400 border-b border-gray-700 pb-2">Triage Manifest (DM)</h2>
        <div className="flex flex-col gap-4">
          {triageData.length === 0 ? (
            <p className="text-sm text-gray-400">Loading manifest...</p>
          ) : (
            triageData.map((item: any) => (
              <div key={item.habitation_id} className="bg-gray-700/50 p-3 rounded shadow border border-gray-600">
                <div className="flex justify-between items-center mb-2">
                  <strong className="text-sm">{item.name}</strong>
                  <span className="bg-red-500/20 text-red-400 border border-red-500/50 text-xs px-2 py-0.5 rounded font-medium">Priority {item.priority}</span>
                </div>
                <div className="text-xs text-gray-300 grid grid-cols-2 gap-1 mb-2">
                  <span>Pop: {item.population}</span>
                  <span>FOS: <span className="font-mono text-red-400">{item.FOS}</span></span>
                  <span>Shelter: {item.assigned_shelter}</span>
                </div>
                <div className="text-[10px] uppercase font-bold text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded inline-block">
                  Status: {item.authorization_status}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
