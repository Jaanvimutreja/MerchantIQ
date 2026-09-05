"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createProduct, createBargain } from "@/lib/api";

const AUDIENCES = ["Everyone", "Regular Customers"];
const OBJECTIVES = [
  "Clear Inventory",
  "Maximize Revenue",
  "Drive Customer Engagement",
];

export default function CreateBargainPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    productName: "",
    originalPrice: "",
    minPrice: "",
    inventory: "",
    durationHours: "",
    audience: AUDIENCES[0],
    objective: OBJECTIVES[0],
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      // Step 1: create the product
      const product = await createProduct({
        name: form.productName.trim(),
        original_price: parseFloat(form.originalPrice),
        inventory: parseInt(form.inventory, 10),
      });

      // Step 2: create the bargain
      const bargain = await createBargain({
        product_id: product.id,
        min_price: parseFloat(form.minPrice),
        duration_hours: parseInt(form.durationHours, 10),
        audience: form.audience,
        objective: form.objective,
      });

      router.push(`/bargain/${bargain.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full px-4 py-2.5 border border-gray-300 rounded-lg text-base text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400 transition-colors";
  const labelClass = "block text-base font-bold text-gray-800 mb-1.5";

  return (
    <div className="max-w-xl mx-auto">
      <a href="/" className="text-base font-semibold text-blue-600 hover:text-blue-800 mb-4 inline-flex items-center gap-1.5 transition-colors">
        ← Back to Dashboard
      </a>

      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-8 shadow-xs">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900 mb-1.5">
          Create Bargain
        </h1>
        <p className="text-base text-gray-600 mb-6 leading-relaxed">
          Set up a new limited-time bargain for a product.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3.5 text-red-700 text-base font-medium mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Product Name */}
          <div>
            <label className={labelClass}>Product Name</label>
            <input
              type="text"
              required
              className={inputClass}
              placeholder="e.g. Wireless Mouse"
              value={form.productName}
              onChange={(e) => update("productName", e.target.value)}
              disabled={submitting}
            />
          </div>

          {/* Original Price + Min Price */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Original Price (₹)</label>
              <input
                type="number"
                required
                min="1"
                step="any"
                className={inputClass}
                placeholder="999"
                value={form.originalPrice}
                onChange={(e) => update("originalPrice", e.target.value)}
                disabled={submitting}
              />
            </div>
            <div>
              <label className={labelClass}>Min Acceptable Price (₹)</label>
              <input
                type="number"
                required
                min="1"
                step="any"
                className={inputClass}
                placeholder="500"
                value={form.minPrice}
                onChange={(e) => update("minPrice", e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>

          {/* Inventory + Duration */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Inventory</label>
              <input
                type="number"
                required
                min="0"
                className={inputClass}
                placeholder="50"
                value={form.inventory}
                onChange={(e) => update("inventory", e.target.value)}
                disabled={submitting}
              />
            </div>
            <div>
              <label className={labelClass}>Duration (hours)</label>
              <input
                type="number"
                required
                min="1"
                className={inputClass}
                placeholder="24"
                value={form.durationHours}
                onChange={(e) => update("durationHours", e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>

          {/* Audience */}
          <div>
            <label className={labelClass}>Audience</label>
            <select
              className={inputClass}
              value={form.audience}
              onChange={(e) => update("audience", e.target.value)}
              disabled={submitting}
            >
              {AUDIENCES.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {/* Objective */}
          <div>
            <label className={labelClass}>Objective</label>
            <select
              className={inputClass}
              value={form.objective}
              onChange={(e) => update("objective", e.target.value)}
              disabled={submitting}
            >
              {OBJECTIVES.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-blue-600 text-white text-base font-bold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {submitting ? "Creating…" : "Create Bargain"}
          </button>
        </form>
      </div>
    </div>
  );
}
