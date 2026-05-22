"use client";

import type { Property } from "../lib/types";

interface Props {
  properties: Property[];
  onSelect?: (property: Property) => void;
  selectedId?: string;
}

export function PropertyTable({ properties, onSelect, selectedId }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left font-semibold text-gray-600">Name</th>
            <th className="px-3 py-2 text-left font-semibold text-gray-600">Type</th>
            <th className="px-3 py-2 text-right font-semibold text-gray-600">Lat</th>
            <th className="px-3 py-2 text-right font-semibold text-gray-600">Lon</th>
            <th className="px-3 py-2 text-left font-semibold text-gray-600">Country</th>
            <th className="px-3 py-2 text-right font-semibold text-gray-600">Year Built</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {properties.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-4 text-center text-gray-400 italic">
                No properties found.
              </td>
            </tr>
          )}
          {properties.map((p) => (
            <tr
              key={p.property_id}
              onClick={() => onSelect?.(p)}
              className={`cursor-pointer hover:bg-blue-50 transition-colors ${
                selectedId === p.property_id ? "bg-blue-100" : ""
              }`}
            >
              <td className="px-3 py-2 font-medium text-blue-700">{p.name}</td>
              <td className="px-3 py-2 capitalize">{p.asset_type}</td>
              <td className="px-3 py-2 text-right font-mono text-xs">{p.latitude.toFixed(4)}</td>
              <td className="px-3 py-2 text-right font-mono text-xs">{p.longitude.toFixed(4)}</td>
              <td className="px-3 py-2">{p.country ?? "—"}</td>
              <td className="px-3 py-2 text-right">{p.year_built ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
