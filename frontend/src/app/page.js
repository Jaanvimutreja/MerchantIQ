"use client";

import { useEffect, useState } from "react";
import { getBargains } from "@/lib/api";

const STATUS_COLORS = {
  ACTIVE: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  EXPIRED: "bg-red-50 text-red-700 border border-red-200",
  APPROVED: "bg-blue-50 text-blue-700 border border-blue-200",
  COMPLETED: "bg-gray-100 text-gray-600 border border-gray-200",
};

function formatExpiry(iso) {
  const d = new Date(iso + "Z");
  return d.toLocaleString();
}

export default function Dashboard() {
  const [bargains, setBargains] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getBargains()
      .then(setBargains)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (bargains === null) {
    return <p className="text-gray-400 text-sm">Loading bargains…</p>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Bargains</h1>
          <p className="text-sm text-gray-500 mt-1">
            {bargains.length === 0
              ? "No bargains yet. Create one to get started."
              : `${bargains.length} bargain${bargains.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <a
          href="/create"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Create Bargain
        </a>
      </div>

      {/* Table */}
      {bargains.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Product</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Original</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Min Price</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Expires</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500"></th>
              </tr>
            </thead>
            <tbody>
              {bargains.map((b) => (
                <tr key={b.id} className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-900 font-medium">#{b.id}</td>
                  <td className="px-4 py-3 text-gray-700">Product #{b.product_id}</td>
                  <td className="px-4 py-3 text-right text-gray-900 font-mono">₹{b.original_price.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-gray-900 font-mono">₹{b.min_price.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_COLORS[b.status] || "bg-gray-100 text-gray-600"}`}>
                      {b.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatExpiry(b.expires_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <a
                      href={`/bargain/${b.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      Open →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
