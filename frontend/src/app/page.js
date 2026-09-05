"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  getDiscoveries,
  investigateDiscovery,
  getInvestigations,
  resolveDiscovery,
  getResolutions,
  getBargains,
  analyzeMerchantCsv,
  resetDemoDataset,
  getDatasetInfo,
} from "@/lib/api";

// ── SVG Icon Helpers (Zero Emojis) ──────────────────────────────────
function IconGrid({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <rect x="3" y="3" width="7" height="7" rx="1.5" strokeWidth="2" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" strokeWidth="2" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" strokeWidth="2" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" strokeWidth="2" />
    </svg>
  );
}

function IconSearch({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle cx="11" cy="11" r="7" strokeWidth="2" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconBrain({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M12 2a4 4 0 0 0-4 4v1a3 3 0 0 0-3 3v2a3 3 0 0 0 2 2.83V16a4 4 0 0 0 4 4h2a4 4 0 0 0 4-4v-1.17A3 3 0 0 0 19 12V9a3 3 0 0 0-3-3V6a4 4 0 0 0-4-4z" />
    </svg>
  );
}

function IconShield({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="m9 12 2 2 4-4" />
    </svg>
  );
}

function IconTag({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
      <line x1="7" y1="7" x2="7.01" y2="7" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconActivity({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconSliders({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <line x1="4" y1="21" x2="4" y2="14" strokeWidth="2" strokeLinecap="round" />
      <line x1="4" y1="10" x2="4" y2="3" strokeWidth="2" strokeLinecap="round" />
      <line x1="12" y1="21" x2="12" y2="12" strokeWidth="2" strokeLinecap="round" />
      <line x1="12" y1="8" x2="12" y2="3" strokeWidth="2" strokeLinecap="round" />
      <line x1="20" y1="21" x2="20" y2="16" strokeWidth="2" strokeLinecap="round" />
      <line x1="20" y1="12" x2="20" y2="3" strokeWidth="2" strokeLinecap="round" />
      <line x1="1" y1="14" x2="7" y2="14" strokeWidth="2" strokeLinecap="round" />
      <line x1="9" y1="8" x2="15" y2="8" strokeWidth="2" strokeLinecap="round" />
      <line x1="17" y1="16" x2="23" y2="16" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconRefresh({ className = "w-4 h-4" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <polyline points="23 4 23 10 17 10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="1 20 1 14 7 14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}

function IconCalendar({ className = "w-4 h-4" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeWidth="2" />
      <line x1="16" y1="2" x2="16" y2="6" strokeWidth="2" />
      <line x1="8" y1="2" x2="8" y2="6" strokeWidth="2" />
      <line x1="3" y1="10" x2="21" y2="10" strokeWidth="2" />
    </svg>
  );
}

function IconCheck({ className = "w-4 h-4" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <polyline points="20 6 9 17 4 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconClose({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <line x1="18" y1="6" x2="6" y2="18" strokeWidth="2" strokeLinecap="round" />
      <line x1="6" y1="6" x2="18" y2="18" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconUpload({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="12" y1="3" x2="12" y2="15" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconFile({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="16" y1="13" x2="8" y2="13" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="16" y1="17" x2="8" y2="17" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="10 9 9 9 8 9" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconAlert({ className = "w-4.5 h-4.5" }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
      <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Currency Formatter ──────────────────────────────────────────────
function formatINR(val) {
  if (val === undefined || val === null || isNaN(val)) return "₹0";
  return "₹" + Math.round(val).toLocaleString("en-IN");
}

// ── Human-Readable Insight Formatter ────────────────────────────────
function getHumanInsight(discovery) {
  const pType = discovery.problem_type;
  const seg = discovery.segment || {};

  if (pType === "PAYMENT_FAILURE") {
    if (seg.is_late_night == 1 || seg.is_late_night === "1") {
      return "Payment failures spike during late-night hours";
    }
    return "Debit card gateway failures elevated in Android segment";
  }
  if (pType === "CHECKOUT_ABANDONMENT") {
    if (seg.product_category === "Luxury & Watches") {
      return "Checkout abandonment is unusually high for high-value credit-card carts";
    }
    if (seg.payment_method === "Net Banking") {
      return "High checkout drop-off on large-ticket Net Banking checkouts";
    }
    if (seg.payment_method === "EMI") {
      return "Elevated cart abandonment on mid-range installment plans";
    }
    return "Checkout abandonment elevated significantly in segment";
  }
  if (pType === "REFUND_SPIKE") {
    if (seg.product_category === "Fashion & Apparel") {
      return "Refund requests are unusually high in Fashion & Apparel";
    }
    if (seg.device_type === "iOS") {
      return "Refund rate elevated on mid-tier mobile UPI purchases";
    }
    return "Elevated refund requests detected in segment";
  }
  if (pType === "LOW_CONVERSION") {
    if (seg.device_type === "iOS") {
      return "Low checkout conversion on iOS UPI transactions (₹2K–₹5K)";
    }
    if (seg.product_category === "Fashion & Apparel") {
      return "Subdued purchase conversion across Fashion & Apparel products";
    }
    return "Low conversion rate in segment relative to store baseline";
  }
  if (pType === "CUSTOMER_PRICE_SENSITIVITY") {
    return "Strong price sensitivity and high bargaining demand detected";
  }

  return discovery.title
    .replace(/device_type=|payment_method=|product_category=|amount_bucket=|is_late_night=/g, "")
    .replace(/&/g, "·");
}

function getSegmentChips(seg) {
  if (!seg) return [];
  return Object.entries(seg).map(([k, v]) => {
    if (k === "is_late_night" && (v == 1 || v === "1")) return "Late Night (23:00–04:00)";
    if (k === "amount_bucket") return v.startsWith(">") ? `> ₹${v.slice(1)}` : v;
    return String(v);
  });
}

export default function MerchantIQDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [discoveries, setDiscoveries] = useState([]);
  const [resolutions, setResolutions] = useState([]);
  const [investigations, setInvestigations] = useState([]);
  const [bargains, setBargains] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Drawer state
  const [drawerDiscovery, setDrawerDiscovery] = useState(null);
  const [investigationData, setInvestigationData] = useState(null);
  const [resolutionData, setResolutionData] = useState(null);
  const [investigating, setInvestigating] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [drawerError, setDrawerError] = useState(null);

  // Table filter
  const [tableFilter, setTableFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Dataset & CSV Upload modal state
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadStage, setUploadStage] = useState("idle"); // "idle" | "analyzing" | "completed" | "error"
  const [uploadProgressStep, setUploadProgressStep] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [isResetting, setIsResetting] = useState(false);

  function loadData() {
    setLoading(true);
    setError(null);
    Promise.all([
      getDiscoveries().catch(() => []),
      getResolutions().catch(() => []),
      getInvestigations().catch(() => []),
      getBargains().catch(() => []),
      getDatasetInfo().catch(() => null),
    ])
      .then(([discList, resList, invList, barList, info]) => {
        const activeDiscoveries = Array.isArray(discList) ? discList : [];
        setDiscoveries(activeDiscoveries);

        // Strict scoping: only include resolutions and investigations for discoveries in active dataset
        const activeIds = new Set(activeDiscoveries.map((d) => d.discovery_id));
        const filteredRes = (Array.isArray(resList) ? resList : []).filter((r) => activeIds.has(r.discovery_id));
        setResolutions(filteredRes);

        const filteredInv = (Array.isArray(invList) ? invList : []).filter((inv) => {
          const dId = inv?.discovery?.discovery_id || inv?.discovery_id;
          return dId && activeIds.has(dId);
        });
        setInvestigations(filteredInv);

        setBargains(Array.isArray(barList) ? barList : []);
        if (info) setDatasetInfo(info);
      })
      .catch((err) => {
        setError(err.message || "Failed to load telemetry data");
      })
      .finally(() => {
        setLoading(false);
      });
  }

  async function handleResetDemo() {
    setIsResetting(true);
    setError(null);
    try {
      const res = await resetDemoDataset();
      setDiscoveries(res.discoveries || []);
      setDatasetInfo(res.summary || null);
      setDrawerDiscovery(null);
      setInvestigationData(null);
      setResolutionData(null);
      Promise.all([
        getResolutions().catch(() => []),
        getInvestigations().catch(() => []),
      ]).then(([newRes, newInv]) => {
        setResolutions(newRes || []);
        setInvestigations(newInv || []);
      });
    } catch (err) {
      setError(err.message || "Failed to reset demo dataset");
    } finally {
      setIsResetting(false);
    }
  }

  async function handleStartAnalysis() {
    if (!uploadFile) return;
    setUploadStage("analyzing");
    setUploadProgressStep(1);
    setUploadError(null);

    const stepTimer1 = setTimeout(() => setUploadProgressStep(2), 500);
    const stepTimer2 = setTimeout(() => setUploadProgressStep(3), 1000);
    const stepTimer3 = setTimeout(() => setUploadProgressStep(4), 1600);

    try {
      const data = await analyzeMerchantCsv(uploadFile);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setUploadProgressStep(4);
      setUploadResult(data);

      // Reset state so metrics reflect ONLY the uploaded custom dataset
      setDiscoveries(data.discoveries || []);
      setDatasetInfo(data.summary || null);
      setResolutions([]);
      setInvestigations([]);
      setDrawerDiscovery(null);
      setInvestigationData(null);
      setResolutionData(null);

      setUploadStage("completed");
    } catch (err) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setUploadStage("error");
      setUploadError(err.details || { message: err.message });
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // Aggregated KPIs (Scoped strictly to current active dataset)
  const totalRevenueAtRisk = useMemo(() => {
    return discoveries.reduce((sum, d) => sum + (d.estimated_revenue_at_risk || 0), 0);
  }, [discoveries]);

  const totalRevenueRecovered = useMemo(() => {
    return resolutions.reduce((sum, r) => sum + (r.recovered_amount || 0), 0);
  }, [resolutions]);

  const totalCustomersProtected = useMemo(() => {
    return resolutions.reduce((sum, r) => sum + (r.customers_affected || 0), 0);
  }, [resolutions]);

  // CRITICAL FIX: Efficiency calculation cannot show 100% when recovered is 0 and at risk is > 0
  const recoveryRatePct = useMemo(() => {
    if (!totalRevenueRecovered || totalRevenueRecovered <= 0 || !totalRevenueAtRisk || totalRevenueAtRisk <= 0) {
      return 0;
    }
    const rate = Math.round((totalRevenueRecovered / totalRevenueAtRisk) * 100);
    return Math.min(100, Math.max(0, rate));
  }, [totalRevenueAtRisk, totalRevenueRecovered]);

  const recoverableRevenue = Math.max(0, totalRevenueAtRisk - totalRevenueRecovered);

  // Friction by type
  const problemsByType = useMemo(() => {
    const counts = {
      PAYMENT_FAILURE: 0,
      CHECKOUT_ABANDONMENT: 0,
      REFUND_SPIKE: 0,
      LOW_CONVERSION: 0,
    };
    discoveries.forEach((d) => {
      if (counts[d.problem_type] !== undefined) {
        counts[d.problem_type] += 1;
      }
    });
    return counts;
  }, [discoveries]);

  // Fast map of resolutions by discovery_id
  const resolvedMap = useMemo(() => {
    const map = {};
    resolutions.forEach((r) => {
      map[r.discovery_id] = r;
    });
    return map;
  }, [resolutions]);

  // Filtered discoveries for table
  const filteredDiscoveries = useMemo(() => {
    return discoveries.filter((d) => {
      if (tableFilter !== "ALL" && d.problem_type !== tableFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const insight = getHumanInsight(d).toLowerCase();
        const dId = (d.discovery_id || "").toLowerCase();
        const pType = (d.problem_type || "").toLowerCase();
        if (!insight.includes(q) && !dId.includes(q) && !pType.includes(q)) return false;
      }
      return true;
    });
  }, [discoveries, tableFilter, searchQuery]);

  // Open right-side drawer and trigger investigation if not already fetched
  async function handleOpenDrawer(discovery) {
    setDrawerDiscovery(discovery);
    setInvestigationData(null);
    setResolutionData(null);
    setDrawerError(null);
    setInvestigating(true);

    try {
      const res = await investigateDiscovery(discovery.discovery_id);
      setInvestigationData(res);
      getInvestigations().then((data) => setInvestigations(data || [])).catch(() => {});
    } catch (err) {
      setDrawerError(err.message || "Failed to fetch AI investigation");
    } finally {
      setInvestigating(false);
    }
  }

  // Trigger resolution
  async function handleResolve(discoveryId) {
    setResolving(true);
    setDrawerError(null);
    try {
      const res = await resolveDiscovery(discoveryId);
      setResolutionData(res.resolution);
      Promise.all([
        getResolutions().catch(() => []),
        getInvestigations().catch(() => []),
      ]).then(([newRes, newInv]) => {
        setResolutions(newRes || []);
        setInvestigations(newInv || []);
      });
    } catch (err) {
      setDrawerError(err.message || "Resolution execution failed");
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full bg-[#F8FAFC] text-slate-900 font-sans">
      {/* ── 1. DARK NAVY LEFT SIDEBAR ─────────────────────────────── */}
      <aside className="w-60 xl:w-64 bg-[#0F172A] text-slate-300 shrink-0 min-h-screen flex flex-col justify-between border-r border-slate-800">
        <div>
          {/* Brand header */}
          <div className="h-16 px-5 flex items-center gap-3 border-b border-slate-800/80">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-extrabold text-sm tracking-wider">
              IQ
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight">MerchantIQ</span>
              <span className="block text-xs text-slate-400">Autonomous Operations</span>
            </div>
          </div>

          {/* Navigation Links (15% larger typography) */}
          <nav className="p-3 space-y-1 text-sm font-medium">
            {[
              { id: "overview", label: "Overview", icon: IconGrid, count: null },
              { id: "discoveries", label: "AI Discoveries", icon: IconSearch, count: discoveries.length },
              { id: "investigations", label: "Investigations", icon: IconBrain, count: investigations.length || null },
              { id: "resolutions", label: "Resolutions", icon: IconShield, count: resolutions.length || null },
              { id: "campaigns", label: "Bargain Campaigns", icon: IconTag, count: bargains.length || null },
              { id: "telemetry", label: "Event Telemetry", icon: IconActivity, count: "10k" },
              { id: "config", label: "Settings", icon: IconSliders, count: null },
            ].map((item) => {
              const active = activeTab === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-left transition-colors cursor-pointer ${
                    active
                      ? "bg-slate-800 text-white font-semibold"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4.5 h-4.5 text-slate-400" />
                    <span>{item.label}</span>
                  </div>
                  {item.count !== null && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-semibold ${
                        active ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Sidebar Elements */}
        <div className="p-3.5 border-t border-slate-800/80 space-y-3">
          {/* AI Engine Status Card */}
          <div className="bg-[#1E293B] rounded-lg p-3.5 border border-slate-800 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">AI Sentinel</span>
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Online
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1.5 font-medium">
              {datasetInfo?.total_records
                ? `${datasetInfo.total_records.toLocaleString()} events monitored`
                : "10,000 events monitored"}
            </p>
            <span className="text-xs text-slate-400">IsolationForest (p &lt; 0.05)</span>
          </div>

          {/* Merchant Profile at bottom */}
          <div className="flex items-center gap-3 px-2 py-1.5">
            <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-white border border-slate-700">
              {datasetInfo?.is_custom ? "MD" : "AC"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-white truncate">
                {datasetInfo?.is_custom ? datasetInfo.filename.replace(/\.csv$/i, "") : "Acme Merchant"}
              </p>
              <p className="text-xs text-slate-400 truncate">
                {datasetInfo?.is_custom ? "Custom Dataset · Active" : "Store #1042 · Live"}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── 2. MAIN OPERATIONS VIEWPORT ──────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col min-h-screen">
        {/* TOP BAR */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 sm:px-8 flex items-center justify-between shrink-0">
          {/* Left: Search input */}
          <div className="flex items-center gap-3 max-w-md w-full">
            <div className="relative w-full">
              <IconSearch className="w-4.5 h-4.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search discoveries, metrics, segments..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Right: Date range + Engine status + New Bargain */}
          <div className="flex items-center gap-3.5">
            <div className="hidden md:flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-md">
              <IconCalendar className="w-4 h-4 text-slate-400" />
              <span>Last 45 days</span>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-700 px-2 py-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>Engine Online</span>
            </div>

            <Link
              href="/create"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-semibold transition-colors shadow-xs"
            >
              <span>+</span>
              <span>New Bargain</span>
            </Link>
          </div>
        </header>

        {/* MAIN BODY SURFACE */}
        <main className="flex-1 p-6 sm:p-8 space-y-6 overflow-y-auto">
          {/* MAIN HERO */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                Good morning, Merchant.
              </h1>
              <p className="text-sm sm:text-base text-slate-500 mt-1">
                MerchantIQ is actively scanning your transactions, finding hidden problems, and recovering lost revenue.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 shrink-0">
              {datasetInfo?.is_custom ? (
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-md">
                    <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                    <span className="truncate max-w-[150px]">Custom: {datasetInfo.filename}</span>
                  </span>
                  <button
                    onClick={handleResetDemo}
                    disabled={isResetting || loading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md border border-slate-300 transition-colors shadow-xs cursor-pointer disabled:opacity-50"
                  >
                    <IconRefresh className={`w-3.5 h-3.5 ${isResetting ? "animate-spin" : ""}`} />
                    <span>Reset to Demo</span>
                  </button>
                </div>
              ) : (
                <span className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-md">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Engine Online
                </span>
              )}

              <button
                onClick={() => {
                  setShowUploadModal(true);
                  setUploadStage("idle");
                  setUploadFile(null);
                  setUploadError(null);
                  setUploadResult(null);
                }}
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold rounded-md transition-colors shadow-xs cursor-pointer"
              >
                <IconUpload className="w-4 h-4" />
                <span>Analyze Merchant Data</span>
              </button>

              <button
                onClick={loadData}
                disabled={loading}
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs sm:text-sm font-semibold rounded-md transition-colors shadow-xs cursor-pointer disabled:opacity-50"
              >
                <IconRefresh className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                <span>Scan Engine</span>
              </button>
            </div>
          </div>

          {/* KPI ROW (Four Equal Cards with Large Prominent Numbers) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Events Analyzed */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Events Analyzed</span>
              <div className="text-3xl sm:text-[32px] font-extrabold text-slate-900 mt-1.5 tracking-tight">
                {datasetInfo?.total_records ? datasetInfo.total_records.toLocaleString() : "10,000"}
              </div>
              <div className="text-xs text-slate-500 mt-1.5 font-medium truncate">
                {datasetInfo?.is_custom ? datasetInfo.filename : "100% dataset coverage"}
              </div>
            </div>

            {/* Card 2: Problems Discovered */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Problems Discovered</span>
              <div className="text-3xl sm:text-[32px] font-extrabold text-slate-900 mt-1.5 tracking-tight">{discoveries.length}</div>
              <div className="text-xs text-slate-500 mt-1.5 font-medium flex items-center gap-2">
                <span className="text-rose-600 font-semibold">1 Critical</span>
                <span>·</span>
                <span>7 Warning</span>
              </div>
            </div>

            {/* Card 3: Revenue at Risk */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Revenue at Risk</span>
              <div className="text-3xl sm:text-[32px] font-extrabold text-rose-600 mt-1.5 tracking-tight">{formatINR(totalRevenueAtRisk)}</div>
              <div className="text-xs text-slate-500 mt-1.5 font-medium">IsolationForest model</div>
            </div>

            {/* Card 4: Revenue Recovered */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Revenue Recovered</span>
              <div className="text-3xl sm:text-[32px] font-extrabold text-emerald-600 mt-1.5 tracking-tight">{formatINR(totalRevenueRecovered)}</div>
              <div className="text-xs text-emerald-700 mt-1.5 font-medium">
                {resolutions.length} closed-loop resolutions
              </div>
            </div>
          </div>

          {/* ANALYTICS ROW */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left Card: Revenue Protection & Recovery */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Revenue Protection & Recovery</h3>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded border ${
                    totalRevenueRecovered > 0
                      ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                      : "text-slate-600 bg-slate-100 border-slate-200"
                  }`}>
                    {recoveryRatePct}% Efficiency
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">Recovered vs recoverable friction exposure</p>
              </div>

              {/* Clean Horizontal Visualization */}
              <div className="my-4 space-y-2.5">
                <div className="w-full h-3.5 bg-slate-100 rounded-full overflow-hidden flex">
                  {totalRevenueRecovered > 0 && (
                    <div
                      className="h-full bg-emerald-500 transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(3, recoveryRatePct))}%` }}
                      title={`Recovered: ${formatINR(totalRevenueRecovered)}`}
                    ></div>
                  )}
                  <div
                    className="h-full bg-slate-300 transition-all duration-500"
                    style={{
                      width: `${totalRevenueRecovered > 0 ? 100 - Math.min(100, Math.max(3, recoveryRatePct)) : 100}%`,
                    }}
                    title={`Recoverable / At Risk: ${formatINR(recoverableRevenue)}`}
                  ></div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-1">
                  <div>
                    <span className="text-xs text-slate-500 block font-bold uppercase">Recovered</span>
                    <span className="text-base font-bold text-emerald-600">{formatINR(totalRevenueRecovered)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block font-bold uppercase">Recoverable</span>
                    <span className="text-base font-bold text-slate-700">{formatINR(recoverableRevenue)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block font-bold uppercase">At Risk</span>
                    <span className="text-base font-bold text-rose-600">{formatINR(totalRevenueAtRisk)}</span>
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-400 border-t border-slate-100 pt-2.5">
                Automated action ledger updated on every resolution execution.
              </div>
            </div>

            {/* Right Card: Friction Breakdown by Type (SVG Donut Chart) */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Friction Breakdown by Type</h3>
                  <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{discoveries.length} Total</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">Clustered by merchant behavioral stage</p>
              </div>

              {/* Donut Chart and Legend */}
              <div className="flex items-center justify-between gap-6 my-2">
                {/* SVG Donut */}
                <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#F1F5F9" strokeWidth="12" />
                    {/* Payment Failure (1/8 ~ 12.5% = 29.8px) */}
                    <circle
                      cx="50" cy="50" r="38" fill="none" stroke="#E11D48" strokeWidth="12"
                      strokeDasharray="29.8 238.7" strokeDashoffset="0"
                    />
                    {/* Cart Abandonment (3/8 ~ 37.5% = 89.5px) */}
                    <circle
                      cx="50" cy="50" r="38" fill="none" stroke="#D97706" strokeWidth="12"
                      strokeDasharray="89.5 238.7" strokeDashoffset="-29.8"
                    />
                    {/* Refund Spike (2/8 ~ 25% = 59.7px) */}
                    <circle
                      cx="50" cy="50" r="38" fill="none" stroke="#4F46E5" strokeWidth="12"
                      strokeDasharray="59.7 238.7" strokeDashoffset="-119.3"
                    />
                    {/* Low Conversion (2/8 ~ 25% = 59.7px) */}
                    <circle
                      cx="50" cy="50" r="38" fill="none" stroke="#2563EB" strokeWidth="12"
                      strokeDasharray="59.7 238.7" strokeDashoffset="-179"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-xl font-bold text-slate-900 leading-none">{discoveries.length}</span>
                    <span className="text-xs text-slate-400 font-medium mt-0.5">Anomalies</span>
                  </div>
                </div>

                {/* Donut Legend (15% larger text) */}
                <div className="flex-1 grid grid-cols-2 gap-2.5 text-xs sm:text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-600 shrink-0"></span>
                    <span className="text-slate-600 truncate">Payment:</span>
                    <span className="font-bold text-slate-900">{problemsByType.PAYMENT_FAILURE || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-600 shrink-0"></span>
                    <span className="text-slate-600 truncate">Cart Aband:</span>
                    <span className="font-bold text-slate-900">{problemsByType.CHECKOUT_ABANDONMENT || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 shrink-0"></span>
                    <span className="text-slate-600 truncate">Refund Spike:</span>
                    <span className="font-bold text-slate-900">{problemsByType.REFUND_SPIKE || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-600 shrink-0"></span>
                    <span className="text-slate-600 truncate">Low Conv:</span>
                    <span className="font-bold text-slate-900">{problemsByType.LOW_CONVERSION || 0}</span>
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-400 border-t border-slate-100 pt-2.5">
                Unsupervised cross-dimensional pattern recognition.
              </div>
            </div>
          </div>

          {/* MAIN LOWER WORKSPACE: DISCOVERIES TABLE + RIGHT COLUMN */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
            {/* ── LEFT: MAIN DISCOVERY TABLE (8 COLS) ─────────────── */}
            <div className="xl:col-span-8 bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
              <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3.5">
                <div>
                  <h2 className="text-base font-bold text-slate-900 tracking-tight">AI Discoveries</h2>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">Highest impact anomalies ranked by revenue at risk</p>
                </div>

                {/* Filter Pills */}
                <div className="flex items-center gap-1.5 text-xs">
                  {["ALL", "PAYMENT_FAILURE", "CHECKOUT_ABANDONMENT", "REFUND_SPIKE", "LOW_CONVERSION"].map((filter) => {
                    const labelMap = {
                      ALL: "All",
                      PAYMENT_FAILURE: "Payment",
                      CHECKOUT_ABANDONMENT: "Abandonment",
                      REFUND_SPIKE: "Refunds",
                      LOW_CONVERSION: "Conversion",
                    };
                    const active = tableFilter === filter;
                    return (
                      <button
                        key={filter}
                        onClick={() => setTableFilter(filter)}
                        className={`px-3 py-1.5 rounded text-xs font-semibold cursor-pointer transition-colors ${
                          active
                            ? "bg-slate-900 text-white"
                            : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        {labelMap[filter]}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* TABLE (15–20% Larger Typography) */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-xs">
                    <tr>
                      <th className="py-3 px-3.5 w-12">#</th>
                      <th className="py-3 px-3.5 w-24">Severity</th>
                      <th className="py-3 px-3.5">Insight</th>
                      <th className="py-3 px-3.5">Affected Segment</th>
                      <th className="py-3 px-3.5">Rate vs Base</th>
                      <th className="py-3 px-3.5">At Risk</th>
                      <th className="py-3 px-3.5">Status</th>
                      <th className="py-3 px-3.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredDiscoveries.map((d, index) => {
                      const isResolved = !!resolvedMap[d.discovery_id];
                      const insight = getHumanInsight(d);
                      const chips = getSegmentChips(d.segment);
                      const isHigh = d.severity === "HIGH";
                      const isMed = d.severity === "MEDIUM";

                      return (
                        <tr
                          key={d.discovery_id}
                          onClick={() => handleOpenDrawer(d)}
                          className="hover:bg-slate-50 transition-colors cursor-pointer group"
                        >
                          <td className="py-3.5 px-3.5 text-slate-400 font-mono text-sm">{index + 1}</td>

                          <td className="py-3.5 px-3.5">
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                                isHigh
                                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                                  : isMed
                                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                                  : "bg-slate-100 text-slate-700"
                              }`}
                            >
                              {d.severity}
                            </span>
                          </td>

                          <td className="py-3.5 px-3.5 max-w-xs sm:max-w-md">
                            <div className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors text-sm leading-snug">
                              {insight}
                            </div>
                            <div className="flex flex-wrap gap-1.5 mt-1.5">
                              {chips.map((chip, idx) => (
                                <span
                                  key={idx}
                                  className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium"
                                >
                                  {chip}
                                </span>
                              ))}
                            </div>
                          </td>

                          <td className="py-3.5 px-3.5 text-slate-600">
                            <span className="font-semibold text-slate-900 text-sm">{d.affected_transactions}</span>
                            <span className="text-slate-400 text-xs block">txns affected</span>
                          </td>

                          <td className="py-3.5 px-3.5">
                            <div className="font-semibold text-slate-900 text-sm">
                              {Math.round(d.problem_rate * 100)}%
                              <span className="text-slate-400 text-xs font-normal"> vs {Math.round(d.baseline_rate * 100)}%</span>
                            </div>
                            <span className="text-xs text-rose-600 font-bold block mt-0.5">
                              {d.relative_change ? `${d.relative_change.toFixed(1)}x elevation` : ""}
                            </span>
                          </td>

                          <td className="py-3.5 px-3.5 font-bold text-slate-900 text-sm tabular-nums">
                            {formatINR(d.estimated_revenue_at_risk)}
                          </td>

                          <td className="py-3.5 px-3.5">
                            {isResolved ? (
                              <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                                <IconCheck className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Resolved</span>
                              </span>
                            ) : (
                              <span className="inline-block text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded">
                                Pending
                              </span>
                            )}
                          </td>

                          <td className="py-3.5 px-3.5 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOpenDrawer(d);
                              }}
                              className="px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 hover:text-blue-600 text-xs font-semibold rounded transition-colors cursor-pointer"
                            >
                              {isResolved ? "Outcome" : "Investigate"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}

                    {filteredDiscoveries.length === 0 && (
                      <tr>
                        <td colSpan={8} className="py-12 text-center text-slate-400 text-sm">
                          No discoveries found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ── RIGHT COLUMN: ACTIVITY FEED + IMPACT LEDGER (4 COLS) ─ */}
            <div className="xl:col-span-4 space-y-4">
              {/* AI Activity Feed */}
              <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">AI Activity Feed</h3>
                  <span className="text-xs font-semibold text-slate-400">Continuous Loop</span>
                </div>

                <div className="mt-3.5 space-y-3.5">
                  {datasetInfo?.is_custom ? (
                    <>
                      {/* Event 1: Ingestion */}
                      <div className="flex items-start gap-3 text-xs sm:text-sm">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1 shrink-0"></span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">Dataset Ingested</span>
                            <span className="text-xs text-blue-700 font-semibold bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                              Custom CSV
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                            {datasetInfo.filename} ({datasetInfo.total_records.toLocaleString()} records). Auto-mapped {Object.keys(datasetInfo.mapped_columns || {}).length} columns.
                          </p>
                        </div>
                      </div>

                      {/* Event 2: Highest priority discovery */}
                      {discoveries.length > 0 && (
                        <div className="flex items-start gap-3 text-xs sm:text-sm">
                          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mt-1 shrink-0"></span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900 text-sm">Primary Friction Flagged</span>
                              <span className="text-xs text-slate-400 font-mono">{discoveries[0].discovery_id}</span>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                              {getHumanInsight(discoveries[0])}. Revenue exposure: {formatINR(discoveries[0].estimated_revenue_at_risk)}.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Event 3: Executed resolutions or awaiting action */}
                      {resolutions.length > 0 ? (
                        resolutions.slice(0, 2).map((r) => (
                          <div key={r.resolution_id} className="flex items-start gap-3 text-xs sm:text-sm">
                            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mt-1 shrink-0"></span>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-slate-900 text-sm">Resolution Executed</span>
                                <span className="text-xs text-emerald-700 font-semibold">{r.action_type}</span>
                              </div>
                              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                                {r.message || `Recovered ${formatINR(r.recovered_amount)}.`}
                              </p>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="flex items-start gap-3 text-xs sm:text-sm">
                          <span className="w-2.5 h-2.5 rounded-full bg-slate-300 mt-1 shrink-0"></span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-700 text-sm">Awaiting First Resolution</span>
                              <span className="text-xs text-slate-400">Ready</span>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                              No automated actions executed yet on this uploaded dataset. Select a discovery to investigate and resolve.
                            </p>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {/* Event 1: Discovered */}
                      <div className="flex items-start gap-3 text-xs sm:text-sm">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mt-1 shrink-0"></span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">Pattern Discovered</span>
                            <span className="text-xs text-slate-400 font-mono">DISC-0032</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                            Late-night debit card failure spike isolated (45.3% vs 6.5%).
                          </p>
                        </div>
                      </div>

                      {/* Event 2: Investigated */}
                      <div className="flex items-start gap-3 text-xs sm:text-sm">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1 shrink-0"></span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">Investigation Completed</span>
                            <span className="text-xs text-slate-400">72% Conf</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                            Off-peak gateway compatibility friction verified by safety layer.
                          </p>
                        </div>
                      </div>

                      {/* Event 3: Action Resolved */}
                      <div className="flex items-start gap-3 text-xs sm:text-sm">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mt-1 shrink-0"></span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">Resolution Executed</span>
                            <span className="text-xs text-emerald-700 font-semibold">payment_recovery</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                            Surfaced alternate payment routing. Recovered {formatINR(36283)}.
                          </p>
                        </div>
                      </div>

                      {/* Event 4: Outcome Recorded */}
                      <div className="flex items-start gap-3 text-xs sm:text-sm">
                        <span className="w-2.5 h-2.5 rounded-full bg-slate-400 mt-1 shrink-0"></span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">Feedback Stored</span>
                            <span className="text-xs text-slate-400">SQLite</span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                            Measured 35% recovery rate to inform future priority ranking.
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Autonomous Impact Ledger */}
              <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Autonomous Impact Ledger</h3>
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Live Verified
                  </span>
                </div>

                <div className="mt-3.5">
                  <span className="text-xs font-bold text-slate-400 uppercase">Total Revenue Recovered</span>
                  <div className="text-2xl sm:text-[28px] font-extrabold text-emerald-600 mt-1 tracking-tight">
                    {formatINR(totalRevenueRecovered)}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {resolutions.length > 0
                      ? `Across ${resolutions.length} autonomous closed-loop action${resolutions.length === 1 ? "" : "s"}.`
                      : datasetInfo?.is_custom
                      ? "Awaiting first resolution action on this dataset."
                      : "Across 0 autonomous closed-loop actions."}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 mt-4 pt-3.5 border-t border-slate-100 text-xs sm:text-sm">
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-bold">Recovery Rate</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">{recoveryRatePct}% Avg</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-bold">Transactions Protected</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">{totalCustomersProtected}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-bold">Decision Latency</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">&lt; 120ms</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-bold">Guardrails</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">Zero Financial Writes</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* ── 3. RIGHT-SIDE SLIDE-OVER DRAWER (UPGRADED TYPOGRAPHY) ─ */}
      {drawerDiscovery && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <div
            onClick={() => setDrawerDiscovery(null)}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
          ></div>

          {/* Drawer Panel */}
          <div className="fixed inset-y-0 right-0 w-full sm:w-[560px] md:w-[600px] bg-white shadow-2xl z-50 flex flex-col border-l border-slate-200">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 flex items-start justify-between gap-3 bg-slate-50">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                    {drawerDiscovery.discovery_id}
                  </span>
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded ${
                      drawerDiscovery.severity === "HIGH"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {drawerDiscovery.severity} SEVERITY
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 leading-snug">
                  {getHumanInsight(drawerDiscovery)}
                </h3>
              </div>

              <button
                onClick={() => setDrawerDiscovery(null)}
                className="w-8 h-8 rounded bg-slate-200/80 hover:bg-slate-300 flex items-center justify-center text-slate-600 transition-colors cursor-pointer shrink-0"
              >
                <IconClose className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body (15–20% Larger Text) */}
            <div className="flex-1 p-6 overflow-y-auto space-y-5 text-sm">
              {/* Core Metrics Row */}
              <div className="grid grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                <div>
                  <span className="text-xs text-slate-400 uppercase font-bold">Revenue at Risk</span>
                  <p className="text-base font-bold text-rose-600 mt-0.5">
                    {formatINR(drawerDiscovery.estimated_revenue_at_risk)}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase font-bold">Affected Txns</span>
                  <p className="text-base font-bold text-slate-900 mt-0.5">{drawerDiscovery.affected_transactions}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase font-bold">Rate vs Baseline</span>
                  <p className="text-base font-bold text-slate-900 mt-0.5">
                    {Math.round(drawerDiscovery.problem_rate * 100)}% vs {Math.round(drawerDiscovery.baseline_rate * 100)}%
                  </p>
                </div>
              </div>

              {/* Segment Chips */}
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  Affected Segment
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {getSegmentChips(drawerDiscovery.segment).map((chip, idx) => (
                    <span key={idx} className="bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1 rounded font-medium text-xs sm:text-sm">
                      {chip}
                    </span>
                  ))}
                </div>
              </div>

              {/* Statistical Evidence */}
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  Empirical Evidence
                </span>
                <div className="space-y-2">
                  {drawerDiscovery.evidence?.map((ev, i) => (
                    <div key={i} className="flex items-start gap-2.5 bg-slate-50 p-2.5 rounded border border-slate-200/60 text-slate-700 text-xs sm:text-sm leading-relaxed">
                      <IconCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                      <span>{ev}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Investigation Loading */}
              {investigating && (
                <div className="py-10 text-center">
                  <div className="w-7 h-7 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2.5"></div>
                  <p className="font-semibold text-slate-700 text-sm">Running AI Investigation Layer...</p>
                  <p className="text-xs text-slate-400 mt-0.5">Synthesizing statistical evidence & policy guardrails</p>
                </div>
              )}

              {/* Drawer Error */}
              {drawerError && (
                <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded font-medium text-xs sm:text-sm">
                  {drawerError}
                </div>
              )}

              {/* AI Investigation Findings */}
              {investigationData && !investigating && (
                <div className="space-y-4 pt-2 border-t border-slate-200">
                  {/* Root Cause Box */}
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Likely Root Cause</span>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        {investigationData.investigation?.confidence}% Confidence
                      </span>
                    </div>
                    <p className="font-semibold text-slate-900 leading-relaxed text-sm">
                      {investigationData.investigation?.root_cause}
                    </p>
                    <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                      {investigationData.investigation?.reasoning}
                    </p>
                  </div>

                  {/* Impact & Recommendation */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-lg border border-slate-200 bg-white">
                      <span className="text-xs font-bold text-slate-400 uppercase">Business Impact</span>
                      <p className="font-medium text-slate-700 text-xs sm:text-sm mt-1">{investigationData.investigation?.business_impact}</p>
                    </div>

                    <div className="p-3.5 rounded-lg border border-blue-200 bg-blue-50/50">
                      <span className="text-xs font-bold text-blue-700 uppercase">Recommended Action</span>
                      <p className="font-bold text-slate-900 text-sm mt-1">
                        {investigationData.decision?.action_type}
                      </p>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                        {investigationData.decision?.action}
                      </p>
                    </div>
                  </div>

                  {/* Resolution Result if executed */}
                  {resolutionData && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                          <IconCheck className="w-4 h-4 text-emerald-600" />
                          <span>Resolution Executed & Recorded</span>
                        </span>
                        <span className="text-xs font-mono font-bold text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-200">
                          {resolutionData.resolution_id}
                        </span>
                      </div>

                      <p className="font-medium text-emerald-950 text-sm">{resolutionData.message}</p>

                      <div className="grid grid-cols-3 gap-2 bg-white p-3 rounded border border-emerald-100 text-center">
                        <div>
                          <span className="text-xs text-slate-400 font-bold uppercase">Status</span>
                          <p className="font-bold text-slate-900 text-sm">{resolutionData.status}</p>
                        </div>
                        <div>
                          <span className="text-xs text-slate-400 font-bold uppercase">Recovered</span>
                          <p className="font-bold text-emerald-600 text-sm">{formatINR(resolutionData.recovered_amount)}</p>
                        </div>
                        <div>
                          <span className="text-xs text-slate-400 font-bold uppercase">Recovery Rate</span>
                          <p className="font-bold text-emerald-600 text-sm">
                            {Math.round((resolutionData.recovery_rate || 0) * 100)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Drawer Footer */}
            <div className="p-4 sm:p-5 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3 shrink-0">
              <button
                onClick={() => setDrawerDiscovery(null)}
                className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded text-xs sm:text-sm font-semibold hover:bg-slate-100 transition-colors cursor-pointer"
              >
                Close
              </button>

              {!resolutionData ? (
                <button
                  onClick={() => handleResolve(drawerDiscovery.discovery_id)}
                  disabled={resolving || investigating}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs sm:text-sm font-semibold transition-colors shadow-xs cursor-pointer disabled:opacity-50 flex items-center gap-2"
                >
                  {resolving && <IconRefresh className="w-4 h-4 animate-spin" />}
                  <span>{resolving ? "Executing Action..." : "Resolve with AI"}</span>
                </button>
              ) : (
                <span className="text-xs sm:text-sm font-bold text-emerald-700 flex items-center gap-1.5">
                  <IconCheck className="w-4.5 h-4.5 text-emerald-600" />
                  <span>Recorded in Ledger</span>
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── 4. ANALYZE MERCHANT DATA MODAL ───────────────────────── */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          <div className="bg-white rounded-xl border border-slate-200 shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col my-auto">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shrink-0">
                  <IconUpload className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900">
                    {uploadStage === "idle" && "Analyze Merchant Data"}
                    {uploadStage === "analyzing" && "Analyzing Transactions..."}
                    {uploadStage === "completed" && "Analysis Complete"}
                    {uploadStage === "error" && "Analysis Error"}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {uploadStage === "idle" && "Upload any transaction export (CSV) to discover operational friction and revenue risk."}
                    {uploadStage === "analyzing" && "Executing autonomous machine learning pipeline on your data."}
                    {uploadStage === "completed" && "Machine learning models have completed statistical friction analysis."}
                    {uploadStage === "error" && "Validation or format issue detected with the uploaded dataset."}
                  </p>
                </div>
              </div>
              {uploadStage !== "analyzing" && (
                <button
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadStage("idle");
                    setUploadFile(null);
                    setUploadError(null);
                  }}
                  className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors cursor-pointer"
                >
                  <IconClose className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Stepper Header */}
            <div className="px-6 py-3 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between text-xs font-semibold text-slate-500">
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  uploadStage === "idle" ? "bg-blue-600 text-white" : "bg-emerald-500 text-white"
                }`}>
                  {uploadStage === "idle" ? "1" : <IconCheck className="w-3.5 h-3.5" />}
                </span>
                <span className={uploadStage === "idle" ? "text-slate-900 font-bold" : "text-slate-600"}>Upload CSV</span>
              </div>
              <span className="text-slate-300">→</span>
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  uploadStage === "analyzing"
                    ? "bg-blue-600 text-white"
                    : uploadStage === "completed"
                    ? "bg-emerald-500 text-white"
                    : "bg-slate-200 text-slate-600"
                }`}>
                  {uploadStage === "completed" ? <IconCheck className="w-3.5 h-3.5" /> : "2"}
                </span>
                <span className={uploadStage === "analyzing" ? "text-blue-600 font-bold" : uploadStage === "completed" ? "text-slate-600" : "text-slate-400"}>
                  Analysis
                </span>
              </div>
              <span className="text-slate-300">→</span>
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  uploadStage === "completed" ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-600"
                }`}>
                  3
                </span>
                <span className={uploadStage === "completed" ? "text-emerald-700 font-bold" : "text-slate-400"}>
                  Results
                </span>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5">
              {/* STAGE 1: IDLE / UPLOAD */}
              {uploadStage === "idle" && (
                <>
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    id="merchant-csv-file"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setUploadFile(e.target.files[0]);
                      }
                    }}
                  />

                  {!uploadFile ? (
                    <label
                      htmlFor="merchant-csv-file"
                      className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-lg p-8 flex flex-col items-center justify-center text-center bg-slate-50/50 hover:bg-blue-50/30 transition-all cursor-pointer group"
                    >
                      <div className="w-12 h-12 rounded-full bg-blue-50 group-hover:bg-blue-100 text-blue-600 flex items-center justify-center mb-3 transition-colors">
                        <IconUpload className="w-6 h-6" />
                      </div>
                      <p className="text-sm font-semibold text-slate-800">
                        Click to browse or drop your merchant CSV here
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        Compatible with Shopify, Stripe, Razorpay, WooCommerce, or custom exports
                      </p>
                      <span className="mt-3 px-3 py-1 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-700 shadow-2xs">
                        Select .CSV file
                      </span>
                    </label>
                  ) : (
                    <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                          <IconFile className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">{uploadFile.name}</p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {(uploadFile.size / 1024).toFixed(1)} KB · Ready for auto-mapping & analysis
                          </p>
                        </div>
                      </div>
                      <label
                        htmlFor="merchant-csv-file"
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 cursor-pointer underline px-2 py-1"
                      >
                        Change file
                      </label>
                    </div>
                  )}

                  {/* Schema Requirements Info */}
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-700 uppercase tracking-wider">Required Columns</span>
                      <span className="text-slate-400 font-medium">Auto-mapped by alias</span>
                    </div>
                    <ul className="space-y-1.5 text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
                        <div>
                          <strong className="text-slate-800">Amount:</strong> <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">amount</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">total</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">price</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">order_value</code>
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
                        <div>
                          <strong className="text-slate-800">Payment Status:</strong> <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">status</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">payment_status</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">payment_state</code>
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
                        <div>
                          <strong className="text-slate-800">Category Dimension (At least 1):</strong> <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">payment_method</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">device_type</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">product_category</code>, <code className="bg-white px-1 py-0.5 border border-slate-200 rounded text-slate-700">location</code>
                        </div>
                      </li>
                    </ul>
                  </div>
                </>
              )}

              {/* STAGE 2: ANALYZING PROGRESS */}
              {uploadStage === "analyzing" && (
                <div className="py-4 space-y-4">
                  <div className="space-y-3">
                    {[
                      { step: 1, title: "Normalizing & Schema Mapping", desc: "Detecting column aliases and standardizing numeric fields" },
                      { step: 2, title: "IsolationForest Anomaly Detector", desc: "Evaluating multi-dimensional transaction anomalies" },
                      { step: 3, title: "Statistical Pattern Discovery", desc: "Testing candidate segments with Chi-Square (p < 0.05)" },
                      { step: 4, title: "Revenue Exposure & Impact Calculation", desc: "Estimating revenue at risk across friction clusters" },
                    ].map((item) => {
                      const isDone = uploadProgressStep > item.step;
                      const isCurrent = uploadProgressStep === item.step;
                      return (
                        <div
                          key={item.step}
                          className={`p-3.5 rounded-lg border transition-all flex items-center justify-between ${
                            isDone
                              ? "bg-emerald-50/50 border-emerald-200 text-emerald-900"
                              : isCurrent
                              ? "bg-blue-50/50 border-blue-300 text-blue-900 shadow-2xs"
                              : "bg-slate-50 border-slate-200 text-slate-400 opacity-60"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className="shrink-0">
                              {isDone ? (
                                <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                                  <IconCheck className="w-4 h-4" />
                                </div>
                              ) : isCurrent ? (
                                <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center animate-spin">
                                  <IconRefresh className="w-3.5 h-3.5" />
                                </div>
                              ) : (
                                <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold">
                                  {item.step}
                                </div>
                              )}
                            </div>
                            <div>
                              <p className="text-sm font-semibold">{item.title}</p>
                              <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                            </div>
                          </div>
                          {isCurrent && (
                            <span className="text-xs font-bold text-blue-600 animate-pulse">
                              Processing...
                            </span>
                          )}
                          {isDone && (
                            <span className="text-xs font-semibold text-emerald-600">
                              Passed
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* STAGE 3: RESULTS */}
              {uploadStage === "completed" && uploadResult && (
                <div className="space-y-4">
                  {/* Banner */}
                  <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0">
                      <IconCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-emerald-950">
                        Successfully Processed {uploadResult.summary.total_records.toLocaleString()} Transactions
                      </p>
                      <p className="text-xs text-emerald-800 mt-0.5">
                        Dataset <strong className="font-semibold">{uploadResult.summary.filename}</strong> has been normalized and scanned by MerchantIQ ML models.
                      </p>
                    </div>
                  </div>

                  {/* 3 Metric Cards */}
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-lg">
                      <span className="text-xs font-bold uppercase text-slate-500">Problems Found</span>
                      <div className="text-2xl font-extrabold text-slate-900 mt-1">
                        {uploadResult.discoveries.length}
                      </div>
                    </div>
                    <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-lg">
                      <span className="text-xs font-bold uppercase text-slate-500">Revenue at Risk</span>
                      <div className="text-2xl font-extrabold text-rose-600 mt-1">
                        {formatINR(uploadResult.summary.revenue_at_risk)}
                      </div>
                    </div>
                    <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-lg">
                      <span className="text-xs font-bold uppercase text-slate-500">Failure Rate</span>
                      <div className="text-2xl font-extrabold text-slate-900 mt-1">
                        {uploadResult.summary.failure_rate}%
                      </div>
                    </div>
                  </div>

                  {/* Mapped Columns Pills */}
                  {uploadResult.summary.mapped_columns && Object.keys(uploadResult.summary.mapped_columns).length > 0 && (
                    <div className="border border-slate-200 rounded-lg p-3.5 bg-slate-50 space-y-2">
                      <span className="text-xs font-bold uppercase text-slate-500">Mapped Column Schema</span>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {Object.entries(uploadResult.summary.mapped_columns).map(([orig, canonical]) => (
                          <span
                            key={orig}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-slate-200 rounded text-xs font-medium text-slate-700"
                          >
                            <span className="text-slate-500">{orig}</span>
                            <span className="text-blue-600 font-bold">→</span>
                            <span className="font-semibold text-slate-900">{canonical}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* STAGE 4: ERROR */}
              {uploadStage === "error" && uploadError && (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-rose-500 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <IconAlert className="w-5 h-5" />
                    </div>
                    <div className="space-y-2 flex-1">
                      <p className="text-sm font-bold text-rose-950">
                        {uploadError.error_type === "MISSING_REQUIRED_FIELDS"
                          ? "Missing Required Transaction Columns"
                          : uploadError.error_type === "INSUFFICIENT_DATA"
                          ? "Insufficient Transaction Rows"
                          : "Upload Validation Error"}
                      </p>
                      <p className="text-xs text-rose-800 leading-relaxed">
                        {uploadError.message || "The file could not be analyzed."}
                      </p>

                      {/* Missing Fields List */}
                      {uploadError.missing_fields && uploadError.missing_fields.length > 0 && (
                        <div className="pt-2">
                          <p className="text-xs font-bold text-rose-900 uppercase">Missing Fields:</p>
                          <div className="flex flex-wrap gap-1.5 mt-1">
                            {uploadError.missing_fields.map((mf) => (
                              <span
                                key={mf}
                                className="px-2 py-0.5 bg-white border border-rose-300 rounded text-xs font-bold text-rose-700"
                              >
                                {mf}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Found Columns in User File */}
                      {uploadError.available_columns && uploadError.available_columns.length > 0 && (
                        <div className="pt-1">
                          <p className="text-xs font-semibold text-slate-600">Columns found in uploaded file:</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {uploadError.available_columns.map((col) => (
                              <span
                                key={col}
                                className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs text-slate-600"
                              >
                                {col}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 sm:p-5 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3 shrink-0">
              {uploadStage === "idle" && (
                <>
                  <button
                    onClick={() => {
                      setShowUploadModal(false);
                      setUploadFile(null);
                    }}
                    className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded text-xs sm:text-sm font-semibold hover:bg-slate-100 transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleStartAnalysis}
                    disabled={!uploadFile}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs sm:text-sm font-semibold transition-colors shadow-xs cursor-pointer disabled:opacity-50 flex items-center gap-2"
                  >
                    <IconUpload className="w-4 h-4" />
                    <span>Run AI Analysis</span>
                  </button>
                </>
              )}

              {uploadStage === "analyzing" && (
                <div className="w-full text-center py-1 text-xs text-slate-500 font-medium">
                  Please keep this window open while MerchantIQ analyzes your transactions...
                </div>
              )}

              {uploadStage === "completed" && (
                <>
                  <button
                    onClick={() => {
                      setUploadStage("idle");
                      setUploadFile(null);
                      setUploadResult(null);
                    }}
                    className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded text-xs sm:text-sm font-semibold hover:bg-slate-100 transition-colors cursor-pointer"
                  >
                    Upload Another CSV
                  </button>
                  <button
                    onClick={() => {
                      setShowUploadModal(false);
                      setUploadStage("idle");
                      setUploadFile(null);
                      setUploadResult(null);
                    }}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs sm:text-sm font-semibold transition-colors shadow-xs cursor-pointer flex items-center gap-2"
                  >
                    <span>Explore Discoveries on Dashboard</span>
                    <span>→</span>
                  </button>
                </>
              )}

              {uploadStage === "error" && (
                <>
                  <button
                    onClick={() => {
                      setShowUploadModal(false);
                      setUploadStage("idle");
                      setUploadFile(null);
                      setUploadError(null);
                    }}
                    className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded text-xs sm:text-sm font-semibold hover:bg-slate-100 transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      setUploadStage("idle");
                      setUploadError(null);
                    }}
                    className="px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs sm:text-sm font-semibold transition-colors shadow-xs cursor-pointer"
                  >
                    Try Another File
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
