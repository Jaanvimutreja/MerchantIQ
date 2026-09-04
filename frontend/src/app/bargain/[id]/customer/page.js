"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getBargain, getOffers, createOffer } from "@/lib/api";

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "Z");
  return d.toLocaleString();
}

const OFFER_STATUS_COLORS = {
  PENDING: "bg-amber-50 text-amber-700",
  APPROVED: "bg-emerald-50 text-emerald-700",
  REJECTED: "bg-red-50 text-red-700",
};

export default function CustomerBargainPage() {
  const params = useParams();
  const id = params.id;

  const [bargain, setBargain] = useState(null);
  const [offers, setOffers] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const [form, setForm] = useState({ name: "", email: "", price: "" });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);

  function loadData() {
    Promise.all([getBargain(id), getOffers(id)])
      .then(([b, o]) => {
        setBargain(b);
        setOffers(o);
      })
      .catch((e) => setLoadError(e.message));
  }

  useEffect(() => {
    loadData();
  }, [id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);
    setSubmitting(true);

    try {
      const offer = await createOffer(id, {
        customer_name: form.name.trim(),
        customer_email: form.email.trim(),
        offered_price: parseFloat(form.price),
      });
      setSubmitSuccess(
        `Offer #${offer.id} submitted for ₹${offer.offered_price.toLocaleString()}`
      );
      setForm({ name: "", email: "", price: "" });
      // Refresh offers list
      const updatedOffers = await getOffers(id);
      setOffers(updatedOffers);
      // Refresh bargain too (status may change)
      const updatedBargain = await getBargain(id);
      setBargain(updatedBargain);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
        <strong>Error:</strong> {loadError}
      </div>
    );
  }

  if (!bargain) {
    return <p className="text-gray-400 text-sm">Loading…</p>;
  }

  const inputClass =
    "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400";

  const isActive = bargain.status === "ACTIVE";

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back link */}
      <a
        href={`/bargain/${id}`}
        className="text-sm text-blue-600 hover:text-blue-800 inline-block"
      >
        ← Merchant View
      </a>

      {/* Bargain Info */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-1">
          <h1 className="text-xl font-semibold text-gray-900">Make an Offer</h1>
          <span
            className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${
              isActive
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {bargain.status}
          </span>
        </div>
        <p className="text-sm text-gray-500 mb-5">Bargain #{bargain.id}</p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500 mb-0.5">Product</p>
            <p className="font-semibold text-gray-900">#{bargain.product_id}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Original Price</p>
            <p className="font-semibold text-gray-900 font-mono">₹{bargain.original_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Min Price</p>
            <p className="font-semibold text-gray-900 font-mono">₹{bargain.min_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500 mb-0.5">Expires</p>
            <p className="font-semibold text-gray-900 text-xs">{formatDate(bargain.expires_at)}</p>
          </div>
        </div>
      </div>

      {/* Offer Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Submit Your Offer</h2>

        {!isActive && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-500 text-sm mb-4">
            This bargain is no longer active. Offers cannot be submitted.
          </div>
        )}

        {submitSuccess && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-emerald-700 text-sm mb-4">
            {submitSuccess}
          </div>
        )}

        {submitError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm mb-4">
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Your Name</label>
            <input
              type="text"
              required
              className={inputClass}
              placeholder="Alice Smith"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              disabled={submitting || !isActive}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              className={inputClass}
              placeholder="alice@example.com"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              disabled={submitting || !isActive}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Offer Amount (₹)
              <span className="ml-2 text-gray-400 font-normal">
                Range: ₹{bargain.min_price.toLocaleString()} – ₹{bargain.original_price.toLocaleString()}
              </span>
            </label>
            <input
              type="number"
              required
              min={bargain.min_price}
              max={bargain.original_price}
              step="any"
              className={inputClass}
              placeholder={`${bargain.min_price}`}
              value={form.price}
              onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
              disabled={submitting || !isActive}
            />
          </div>
          <button
            type="submit"
            disabled={submitting || !isActive}
            className="w-full py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Submitting…" : "Submit Offer"}
          </button>
        </form>
      </div>

      {/* Existing Offers */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">
          All Offers
          {offers && <span className="ml-2 text-gray-400 font-normal text-sm">({offers.length})</span>}
        </h2>

        {offers && offers.length === 0 && (
          <p className="text-sm text-gray-400">No offers yet. Be the first!</p>
        )}

        {offers && offers.length > 0 && (
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-2.5 font-medium text-gray-500">Customer</th>
                  <th className="text-right px-4 py-2.5 font-medium text-gray-500">Offered</th>
                  <th className="text-left px-4 py-2.5 font-medium text-gray-500">Status</th>
                  <th className="text-left px-4 py-2.5 font-medium text-gray-500">Time</th>
                </tr>
              </thead>
              <tbody>
                {offers.map((o) => (
                  <tr key={o.id} className="border-b border-gray-100 last:border-b-0">
                    <td className="px-4 py-2.5 text-gray-900">{o.customer_name}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-gray-900">₹{o.offered_price.toLocaleString()}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${OFFER_STATUS_COLORS[o.status] || "bg-gray-100 text-gray-600"}`}>
                        {o.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-400 text-xs">{formatDate(o.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
