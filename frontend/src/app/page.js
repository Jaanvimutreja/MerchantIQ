"use client";

import { useEffect, useState } from "react";
import { getBargains, getProducts } from "@/lib/api";

const STATUS_STYLES = {
  ACTIVE: {
    badge: "bg-emerald-50 text-emerald-800 border-emerald-200 ring-1 ring-emerald-500/20",
    dot: "bg-emerald-500 animate-pulse",
    label: "Active Window",
  },
  APPROVED: {
    badge: "bg-blue-50 text-blue-800 border-blue-200 ring-1 ring-blue-500/20",
    dot: "bg-blue-600",
    label: "Deal Approved",
  },
  COMPLETED: {
    badge: "bg-purple-50 text-purple-800 border-purple-200 ring-1 ring-purple-500/20",
    dot: "bg-purple-600",
    label: "Settled / Paid",
  },
  EXPIRED: {
    badge: "bg-gray-100 text-gray-700 border-gray-200",
    dot: "bg-gray-400",
    label: "Expired",
  },
};

export default function Dashboard() {
  const [bargains, setBargains] = useState(null);
  const [productMap, setProductMap] = useState({});
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  function loadData() {
    setLoading(true);
    setError(null);
    Promise.all([getBargains(), getProducts().catch(() => [])])
      .then(([bList, pList]) => {
        setBargains(bList || []);
        const pMap = {};
        if (Array.isArray(pList)) {
          pList.forEach((p) => {
            pMap[p.id] = p.name;
          });
        }
        setProductMap(pMap);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    setMounted(true);
    loadData();
  }, []);

  function formatExpiry(iso) {
    if (!iso) return "—";
    if (!mounted) return iso.slice(0, 16).replace("T", " ");
    try {
      const d = new Date(iso + "Z");
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-sm text-red-700">
        <h3 className="font-semibold text-base text-red-900 mb-1">Failed to load dashboard</h3>
        <p className="mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (bargains === null && loading) {
    return (
      <div className="py-20 text-center">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium text-gray-500">Loading merchant operations dashboard…</p>
      </div>
    );
  }

  const allBargains = bargains || [];
  const activeCount = allBargains.filter((b) => b.status === "ACTIVE").length;
  const approvedCount = allBargains.filter((b) => b.status === "APPROVED").length;
  const completedCount = allBargains.filter((b) => b.status === "COMPLETED").length;
  const expiredCount = allBargains.filter((b) => b.status === "EXPIRED").length;

  const filteredBargains = allBargains.filter((b) => {
    if (statusFilter === "ALL") return true;
    return b.status === statusFilter;
  });

  return (
    <div className="space-y-9">
      {/* ── 1. Header & Introduction ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
              Operations Console
            </span>
            <span className="text-gray-400">•</span>
            <span className="text-sm sm:text-base font-medium text-gray-600">
              Live SQLite Database • AI Deal Strategist
            </span>
          </div>
          <h1 className="text-3xl sm:text-[40px] sm:leading-tight font-extrabold tracking-tight text-gray-900">
            Bargain Campaigns
          </h1>
          <p className="text-base sm:text-lg text-gray-600 mt-2 max-w-2xl leading-relaxed">
            Manage your time-limited bargaining campaigns. Review verified customer counter-offers,
            evaluate AI deal recommendations, and execute approved deals securely.
          </p>
        </div>

        {/* ── 2. Primary Create Bargain CTA ── */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadData}
            title="Refresh latest data from backend"
            className="p-3 text-gray-600 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-xs"
          >
            <span className="text-lg font-semibold">↻</span>
          </button>
          <a
            href="/create"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white text-base sm:text-lg font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <span className="text-xl leading-none font-bold">+</span>
            <span>Create Bargain</span>
          </a>
        </div>
      </div>

      {/* ── 3. Compact Overview / Metrics Section (Strictly Real Data) ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {/* Total Campaigns */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1.5">
            Total Campaigns
          </p>
          <div className="flex items-baseline justify-between">
            <span className="text-4xl sm:text-5xl font-extrabold font-mono text-gray-900">
              {allBargains.length}
            </span>
            <span className="text-xs sm:text-sm text-gray-400 font-medium">All time</span>
          </div>
          <p className="text-sm sm:text-base text-gray-500 mt-2">All product bargains created</p>
        </div>

        {/* Active Windows */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-emerald-700 mb-1.5 flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            Active Deals
          </p>
          <div className="flex items-baseline justify-between">
            <span className="text-4xl sm:text-5xl font-extrabold font-mono text-emerald-700">
              {activeCount}
            </span>
            <span className="text-xs sm:text-sm text-emerald-600 font-bold font-mono">Live</span>
          </div>
          <p className="text-sm sm:text-base text-gray-500 mt-2">Accepting customer offers</p>
        </div>

        {/* Approved Deals */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-blue-700 mb-1.5 flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
            Merchant Approved
          </p>
          <div className="flex items-baseline justify-between">
            <span className="text-4xl sm:text-5xl font-extrabold font-mono text-blue-700">
              {approvedCount}
            </span>
            <span className="text-xs sm:text-sm text-blue-600 font-bold">Ready</span>
          </div>
          <p className="text-sm sm:text-base text-gray-500 mt-2">Awaiting payment checkout</p>
        </div>

        {/* Completed & Settled */}
        <div className="bg-white p-5 sm:p-6 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-purple-700 mb-1.5 flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600"></span>
            Settled Deals
          </p>
          <div className="flex items-baseline justify-between">
            <span className="text-4xl sm:text-5xl font-extrabold font-mono text-purple-700">
              {completedCount}
            </span>
            <span className="text-xs sm:text-sm text-purple-600 font-bold">Paid</span>
          </div>
          <p className="text-sm sm:text-base text-gray-500 mt-2">Confirmed by backend webhook</p>
        </div>
      </div>

      {/* ── 4. "Your Bargains" Section Header & Filter Tabs ── */}
      <div id="your-bargains" className="space-y-4 pt-2 sm:pt-4 scroll-mt-24">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900">Your Bargains</h2>
            <span className="text-sm sm:text-base font-bold text-gray-600 bg-gray-100 px-3 py-0.5 rounded-full border border-gray-200">
              {filteredBargains.length} {filteredBargains.length === 1 ? "deal" : "deals"}
            </span>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-lg border border-gray-200 text-sm font-bold overflow-x-auto">
            <button
              onClick={() => setStatusFilter("ALL")}
              className={`px-4 py-2 rounded-md transition-colors ${
                statusFilter === "ALL"
                  ? "bg-white text-gray-900 shadow-xs"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              All ({allBargains.length})
            </button>
            <button
              onClick={() => setStatusFilter("ACTIVE")}
              className={`px-4 py-2 rounded-md transition-colors ${
                statusFilter === "ACTIVE"
                  ? "bg-white text-emerald-800 shadow-xs"
                  : "text-gray-600 hover:text-emerald-800"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setStatusFilter("APPROVED")}
              className={`px-4 py-2 rounded-md transition-colors ${
                statusFilter === "APPROVED"
                  ? "bg-white text-blue-800 shadow-xs"
                  : "text-gray-600 hover:text-blue-800"
              }`}
            >
              Approved ({approvedCount})
            </button>
            <button
              onClick={() => setStatusFilter("COMPLETED")}
              className={`px-4 py-2 rounded-md transition-colors ${
                statusFilter === "COMPLETED"
                  ? "bg-white text-purple-800 shadow-xs"
                  : "text-gray-600 hover:text-purple-800"
              }`}
            >
              Completed ({completedCount})
            </button>
            {expiredCount > 0 && (
              <button
                onClick={() => setStatusFilter("EXPIRED")}
                className={`px-4 py-2 rounded-md transition-colors ${
                  statusFilter === "EXPIRED"
                    ? "bg-white text-red-800 shadow-xs"
                    : "text-gray-600 hover:text-red-800"
                }`}
              >
                Expired ({expiredCount})
              </button>
            )}
          </div>
        </div>

        {/* ── 5. Bargains List / Real Data Table ── */}
        {filteredBargains.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-xs scroll-mt-24">
            <div className="w-14 h-14 rounded-full bg-blue-50 border border-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-4 text-2xl font-bold">
              🏷️
            </div>
            <h3 className="text-xl font-extrabold text-gray-900 mb-1.5">
              {allBargains.length === 0
                ? "No bargain campaigns created yet"
                : `No bargains matching "${statusFilter}"`}
            </h3>
            <p className="text-base text-gray-600 max-w-md mx-auto mb-6 leading-relaxed">
              {allBargains.length === 0
                ? "Launch your first dynamic bargaining campaign to start accepting real customer price bids."
                : "Try switching filter tabs or create a new bargain campaign."}
            </p>
            <a
              href="/create"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white text-base font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-xs"
            >
              <span>+ Create First Bargain</span>
            </a>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-xs scroll-mt-24">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[1000px] xl:min-w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50/90 text-xs sm:text-sm font-bold text-gray-600 uppercase tracking-wider">
                    <th className="py-4 pl-5 pr-2 w-16 whitespace-nowrap">Deal ID</th>
                    <th className="py-4 px-3 sm:px-4 min-w-[260px] lg:min-w-[300px]">Product & Strategy</th>
                    <th className="py-4 px-3 text-right whitespace-nowrap">Original Price</th>
                    <th className="py-4 px-3 text-right whitespace-nowrap">Floor Price</th>
                    <th className="py-4 px-3 whitespace-nowrap">Campaign Status</th>
                    <th className="py-4 px-3 whitespace-nowrap">Expires</th>
                    <th className="py-4 pl-3 pr-5 text-right whitespace-nowrap">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredBargains.map((b) => {
                    const statusConfig = STATUS_STYLES[b.status] || STATUS_STYLES.EXPIRED;
                    const productName = productMap[b.product_id] || `Product #${b.product_id}`;
                    const discountPercent =
                      b.original_price > 0
                        ? Math.round(((b.original_price - b.min_price) / b.original_price) * 100)
                        : 0;

                    return (
                      <tr
                        key={b.id}
                        className="hover:bg-gray-50/70 transition-colors group"
                      >
                        {/* ID */}
                        <td className="py-4.5 pl-5 pr-2 font-mono text-base font-semibold text-gray-500 whitespace-nowrap">
                          #{b.id}
                        </td>

                        {/* Product & Strategy */}
                        <td className="py-4.5 px-3 sm:px-4 min-w-[260px] lg:min-w-[300px]">
                          <div className="font-extrabold text-lg sm:text-xl text-gray-900 group-hover:text-blue-600 transition-colors leading-snug">
                            {productName}
                          </div>
                          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                            <span className="text-xs sm:text-sm text-gray-500 font-mono">
                              SKU #{b.product_id}
                            </span>
                            {b.objective && (
                              <span className="text-xs sm:text-sm font-semibold text-gray-700 bg-gray-100 px-2.5 py-0.5 rounded border border-gray-200">
                                {b.objective}
                              </span>
                            )}
                            {b.audience && b.audience !== "Everyone" && (
                              <span className="text-xs sm:text-sm font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200">
                                {b.audience}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Original Price */}
                        <td className="py-4.5 px-3 text-right font-mono font-semibold text-base sm:text-lg text-gray-500 whitespace-nowrap">
                          ₹{b.original_price.toLocaleString()}
                        </td>

                        {/* Floor Price */}
                        <td className="py-4.5 px-3 text-right whitespace-nowrap">
                          <span className="font-mono font-black text-xl sm:text-2xl text-gray-900">
                            ₹{b.min_price.toLocaleString()}
                          </span>
                          <span className="block text-xs sm:text-sm font-bold text-emerald-700">
                            Up to {discountPercent}% off
                          </span>
                        </td>

                        {/* Status Badge */}
                        <td className="py-4.5 px-3 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-2 px-3.5 py-1.5 text-xs sm:text-sm font-bold rounded-full border ${statusConfig.badge}`}
                          >
                            <span className={`w-2.5 h-2.5 rounded-full ${statusConfig.dot}`}></span>
                            {statusConfig.label}
                          </span>
                        </td>

                        {/* Expiry */}
                        <td className="py-4.5 px-3 whitespace-nowrap">
                          <div className="text-sm sm:text-base font-bold text-gray-800">
                            {formatExpiry(b.expires_at)}
                          </div>
                          <span className="text-xs sm:text-sm text-gray-500">
                            {b.duration_hours}h duration
                          </span>
                        </td>

                        {/* Actions */}
                        <td className="py-4.5 pl-3 pr-5 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <a
                              href={`/bargain/${b.id}`}
                              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white rounded-lg text-sm sm:text-base font-bold transition-all border border-blue-200 hover:border-blue-600 shadow-xs"
                            >
                              <span>Manage</span>
                              <span className="text-base leading-none">→</span>
                            </a>
                            <a
                              href={`/bargain/${b.id}/customer`}
                              target="_blank"
                              rel="noreferrer"
                              title="Open public customer bidding view"
                              className="inline-flex items-center px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg text-sm sm:text-base font-semibold transition-colors border border-transparent hover:border-gray-200"
                            >
                              <span>Customer View ↗</span>
                            </a>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ── 6. Operational Workflow Guide (5-Step BargainAI Journey) ── */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-5 border-b border-gray-100">
          <div>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
              BargainAI Merchant Journey
            </h3>
            <p className="text-sm sm:text-base text-gray-600 mt-1 font-medium">
              Create → Customer Offers → AI Evaluation → Human Approval → Payment/Sale
            </p>
          </div>
          <span className="self-start sm:self-auto text-sm sm:text-base font-bold text-blue-700 bg-blue-50 px-3.5 py-1 rounded-md border border-blue-200">
            5-Step Automated Flow
          </span>
        </div>

        {/* 5 Connected Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Step 1 */}
          <div className="p-4 sm:p-5 bg-gray-50/90 rounded-xl border border-gray-200 flex flex-col justify-between relative group hover:border-blue-300 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs sm:text-sm font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  01
                </span>
                <span className="hidden lg:inline text-sm font-bold text-gray-400 group-hover:text-blue-500 transition-colors">
                  →
                </span>
              </div>
              <h4 className="font-extrabold text-base sm:text-lg text-gray-900 mb-1.5">
                01 — Create Bargain
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Set product price floor, duration, inventory limit, and merchant business objective.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-4 sm:p-5 bg-gray-50/90 rounded-xl border border-gray-200 flex flex-col justify-between relative group hover:border-blue-300 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs sm:text-sm font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  02
                </span>
                <span className="hidden lg:inline text-sm font-bold text-gray-400 group-hover:text-blue-500 transition-colors">
                  →
                </span>
              </div>
              <h4 className="font-extrabold text-base sm:text-lg text-gray-900 mb-1.5">
                02 — Customers Make Offers
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Real buyers submit binding price counter-offers recorded directly in the database.
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="p-4 sm:p-5 bg-gray-50/90 rounded-xl border border-gray-200 flex flex-col justify-between relative group hover:border-blue-300 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs sm:text-sm font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  03
                </span>
                <span className="hidden lg:inline text-sm font-bold text-gray-400 group-hover:text-blue-500 transition-colors">
                  →
                </span>
              </div>
              <h4 className="font-extrabold text-base sm:text-lg text-gray-900 mb-1.5">
                03 — AI Evaluates
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Gemini Flash analyzes margins and strategy to recommend the single best eligible offer.
              </p>
            </div>
          </div>

          {/* Step 4 */}
          <div className="p-4 sm:p-5 bg-gray-50/90 rounded-xl border border-gray-200 flex flex-col justify-between relative group hover:border-blue-300 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs sm:text-sm font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  04
                </span>
                <span className="hidden lg:inline text-sm font-bold text-gray-400 group-hover:text-blue-500 transition-colors">
                  →
                </span>
              </div>
              <h4 className="font-extrabold text-base sm:text-lg text-gray-900 mb-1.5">
                04 — Merchant Approves
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Merchant explicitly approves an offer with concurrency-safe database versioning.
              </p>
            </div>
          </div>

          {/* Step 5 */}
          <div className="p-4 sm:p-5 bg-gray-50/90 rounded-xl border border-gray-200 flex flex-col justify-between relative group hover:border-blue-300 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs sm:text-sm font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  05
                </span>
                <span className="hidden lg:inline text-sm font-bold text-emerald-600 font-mono">
                  ✓
                </span>
              </div>
              <h4 className="font-extrabold text-base sm:text-lg text-gray-900 mb-1.5">
                05 — Payment & Sale
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Razorpay Test Mode checkout handles payment; backend webhook validates and marks completed.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
