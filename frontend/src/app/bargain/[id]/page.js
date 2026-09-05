"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getBargain, getOffers, getAuditLog, getRecommendation, approveOffer, rejectOffer, createPaymentOrder } from "@/lib/api";


const STATUS_COLORS = {
  ACTIVE: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  EXPIRED: "bg-red-50 text-red-700 border border-red-200",
  APPROVED: "bg-blue-50 text-blue-700 border border-blue-200",
  COMPLETED: "bg-gray-100 text-gray-600 border border-gray-200",
};

const OFFER_STATUS_COLORS = {
  PENDING: "bg-amber-50 text-amber-700",
  APPROVED: "bg-emerald-50 text-emerald-700",
  REJECTED: "bg-red-50 text-red-700",
};

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "Z");
  return d.toLocaleString();
}

function loadRazorpay() {
  return new Promise((resolve) => {
    if (typeof window !== "undefined" && window.Razorpay) {
      return resolve(true);
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function BargainDetailPage() {
  const params = useParams();
  const id = params.id;

  const [bargain, setBargain] = useState(null);
  const [offers, setOffers] = useState(null);
  const [audit, setAudit] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [recLoading, setRecLoading] = useState(false);
  const [recError, setRecError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [error, setError] = useState(null);

  async function refreshAll() {
    try {
      const [b, o, a] = await Promise.all([getBargain(id), getOffers(id), getAuditLog(id)]);
      setBargain(b);
      setOffers(o);
      setAudit(a);
    } catch (err) {
      setError(err.message);
    }
  }

  function loadRecommendation() {
    setRecLoading(true);
    setRecError(null);
    getRecommendation(id)
      .then((rec) => {
        setRecommendation(rec);
        getAuditLog(id).then(setAudit).catch(() => {});
      })
      .catch((err) => {
        setRecError(err.message);
      })
      .finally(() => {
        setRecLoading(false);
      });
  }

  async function handleApprove(offerId) {
    setActionLoading(offerId);
    setActionMessage(null);
    try {
      const res = await approveOffer(id, offerId);
      setActionMessage({ type: "success", text: res.message || "Offer approved successfully!" });
      await refreshAll();
    } catch (err) {
      setActionMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject(offerId) {
    setActionLoading(offerId);
    setActionMessage(null);
    try {
      const res = await rejectOffer(id, offerId);
      setActionMessage({ type: "success", text: res.message || "Offer rejected." });
      await refreshAll();
    } catch (err) {
      setActionMessage({ type: "error", text: err.message });
    } finally {
      setActionLoading(null);
    }
  }

  async function handlePayNow(offerId) {
    setPaymentLoading(true);
    setActionMessage(null);
    try {
      const orderData = await createPaymentOrder(id, offerId);
      const loaded = await loadRazorpay();
      if (!loaded || !window.Razorpay) {
        setActionMessage({
          type: "error",
          text: "Failed to load Razorpay SDK. Please check your connection.",
        });
        return;
      }

      const approvedOffer = offers?.find((o) => o.id === offerId);
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "BargainAI",
        description: `Bargain #${id} Payment for ${approvedOffer?.customer_name || "Offer"}`,
        order_id: orderData.razorpay_order_id,
        prefill: {
          name: approvedOffer?.customer_name || "",
          email: approvedOffer?.customer_email || "",
        },
        theme: {
          color: "#2563eb",
        },
        handler: function (response) {
          setActionMessage({
            type: "success",
            text: `Payment initiated (Payment ID: ${response.razorpay_payment_id}). Awaiting backend webhook confirmation.`,
          });
          refreshAll();
        },
        modal: {
          ondismiss: function () {
            setPaymentLoading(false);
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      setActionMessage({ type: "error", text: err.message });
    } finally {
      setPaymentLoading(false);
    }
  }

  useEffect(() => {
    Promise.all([getBargain(id), getOffers(id), getAuditLog(id)])
      .then(([b, o, a]) => {
        setBargain(b);
        setOffers(o);
        setAudit(a);
        // Automatically attempt to fetch recommendation if there are pending offers
        const hasPending = o && o.some((offer) => offer.status === "PENDING");
        if (hasPending && b.status === "ACTIVE") {
          loadRecommendation();
        }
      })
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-base font-medium">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (!bargain) {
    return <p className="text-gray-500 text-base">Loading bargain…</p>;
  }

  return (
    <div className="space-y-7">
      {/* Back link */}
      <a href="/" className="text-base font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1.5 transition-colors">
        ← Back to Dashboard
      </a>

      {/* Action Feedback Message */}
      {actionMessage && (
        <div
          className={`p-4 rounded-xl text-base font-medium border ${
            actionMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {actionMessage.text}
        </div>
      )}

      {/* Approved Deal Banner */}
      {bargain.status === "APPROVED" && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block px-3 py-1 text-xs sm:text-sm font-bold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 uppercase tracking-wider">
              DEAL APPROVED
            </span>
            <span className="text-sm sm:text-base text-emerald-800 font-semibold">
              Merchant Confirmed
            </span>
          </div>
          {(() => {
            const approvedOffer = offers?.find((o) => o.status === "APPROVED");
            return (
              approvedOffer && (
                <div className="mt-2 text-emerald-900">
                  <p className="font-extrabold text-lg sm:text-xl">
                    Accepted Offer: ₹{approvedOffer.offered_price.toLocaleString()} from {approvedOffer.customer_name} ({approvedOffer.customer_email})
                  </p>
                  <p className="text-xs sm:text-sm text-emerald-700 mt-1 font-medium">
                    Offer ID #{approvedOffer.id} • Bargain Version #{bargain.version}
                  </p>
                </div>
              )
            );
          })()}
          <div className="mt-4 pt-3 border-t border-emerald-200 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm sm:text-base text-emerald-900 font-semibold">
                Ready for payment via Razorpay Test Mode.
              </p>
              <p className="text-xs sm:text-sm text-emerald-700 mt-0.5">
                Completion will be confirmed by backend webhook verification.
              </p>
            </div>
            {(() => {
              const approvedOffer = offers?.find((o) => o.status === "APPROVED");
              return (
                approvedOffer && (
                  <button
                    onClick={() => handlePayNow(approvedOffer.id)}
                    disabled={paymentLoading}
                    className="px-5 py-2.5 bg-blue-600 text-white text-base font-bold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 inline-flex items-center gap-2 shadow-sm"
                  >
                    {paymentLoading ? "Initiating Order…" : "Pay Now (Razorpay Test Mode) →"}
                  </button>
                )
              );
            })()}
          </div>
        </div>
      )}

      {/* Completed Deal Banner */}
      {bargain.status === "COMPLETED" && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block px-3 py-1 text-xs sm:text-sm font-bold rounded-full bg-blue-100 text-blue-800 border border-blue-300 uppercase tracking-wider">
              DEAL COMPLETED
            </span>
            <span className="text-sm sm:text-base text-blue-800 font-semibold">
              Payment Verified via Webhook
            </span>
          </div>
          {(() => {
            const acceptedOffer = offers?.find((o) => o.status === "APPROVED");
            return (
              acceptedOffer && (
                <div className="mt-2 text-blue-900">
                  <p className="font-extrabold text-lg sm:text-xl">
                    Paid: ₹{acceptedOffer.offered_price.toLocaleString()} by {acceptedOffer.customer_name} ({acceptedOffer.customer_email})
                  </p>
                  <p className="text-xs sm:text-sm text-blue-700 mt-1 font-medium">
                    Offer ID #{acceptedOffer.id} • Deal finalized and verified in audit log.
                  </p>
                </div>
              )
            );
          })()}
        </div>
      )}

      {/* Bargain Info Card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-7 shadow-xs">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900">
              Bargain #{bargain.id}
            </h1>
            <p className="text-base text-gray-500 font-medium mt-1">Product SKU #{bargain.product_id}</p>
          </div>
          <span
            className={`inline-block px-3.5 py-1.5 text-xs sm:text-sm font-bold rounded-full border ${STATUS_COLORS[bargain.status] || "bg-gray-100 text-gray-600 border-gray-200"}`}
          >
            {bargain.status}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
          <div>
            <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Original Price</p>
            <p className="font-bold text-gray-900 font-mono text-xl sm:text-2xl">₹{bargain.original_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Min Acceptable</p>
            <p className="font-bold text-gray-900 font-mono text-xl sm:text-2xl">₹{bargain.min_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Duration</p>
            <p className="font-bold text-gray-900 text-xl sm:text-2xl">{bargain.duration_hours}h</p>
          </div>
          <div>
            <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Expires</p>
            <p className="font-semibold text-gray-900 text-sm sm:text-base leading-snug">{formatDate(bargain.expires_at)}</p>
          </div>
        </div>

        {(bargain.audience || bargain.objective) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5 pt-5 border-t border-gray-100">
            {bargain.audience && (
              <div>
                <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Target Audience</p>
                <p className="text-base font-semibold text-gray-900">{bargain.audience}</p>
              </div>
            )}
            {bargain.objective && (
              <div>
                <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Objective</p>
                <p className="text-base font-semibold text-gray-900">{bargain.objective}</p>
              </div>
            )}
          </div>
        )}

        {/* Customer View button */}
        <div className="mt-6 pt-5 border-t border-gray-100 flex gap-3">
          <a
            href={`/bargain/${bargain.id}/customer`}
            className="inline-flex items-center px-5 py-2.5 bg-blue-600 text-white text-base font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-xs"
          >
            Open Customer View →
          </a>
        </div>
      </div>

      {/* AI Deal Strategist */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-7 shadow-xs">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900">AI Deal Strategist</h2>
            <p className="text-sm text-gray-500 font-medium mt-0.5">
              Powered by Gemini Flash • Evaluates real pending offers against your objective
            </p>
          </div>
          <button
            onClick={loadRecommendation}
            disabled={recLoading}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 shadow-xs"
          >
            {recLoading ? "Analyzing…" : "↻ Refresh Recommendation"}
          </button>
        </div>

        {recLoading && (
          <div className="py-8 text-center text-base font-medium text-gray-500">
            Analyzing pending offers with Gemini Flash…
          </div>
        )}

        {!recLoading && recError && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-base text-gray-700 font-medium">
            {recError}
          </div>
        )}

        {!recLoading && !recError && recommendation && (
          <div className="space-y-5">
            <div className="flex items-center gap-2.5">
              <span
                className={`inline-block px-3 py-1 text-xs sm:text-sm font-bold rounded-full ${
                  recommendation.is_fallback
                    ? "bg-amber-100 text-amber-800 border border-amber-200"
                    : "bg-blue-100 text-blue-800 border border-blue-200"
                }`}
              >
                {recommendation.is_fallback
                  ? "Deterministic Fallback"
                  : "AI Recommended (Gemini Flash)"}
              </span>
              <span className="text-sm text-gray-500 font-semibold">
                Confidence: {Math.round(recommendation.confidence * 100)}%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-5 bg-gray-50 rounded-xl border border-gray-200">
              <div>
                <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Recommended Customer</p>
                <p className="text-lg sm:text-xl font-extrabold text-gray-900">
                  {recommendation.customer_name || `Offer #${recommendation.recommended_offer_id}`}
                </p>
                <p className="text-xs sm:text-sm text-gray-500 font-mono mt-0.5">Offer ID #{recommendation.recommended_offer_id}</p>
              </div>
              <div>
                <p className="text-xs sm:text-sm font-bold uppercase tracking-wider text-gray-500 mb-1">Recommended Amount</p>
                <p className="text-2xl sm:text-3xl font-black font-mono text-gray-900">
                  ₹{recommendation.offered_price ? recommendation.offered_price.toLocaleString() : "—"}
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm sm:text-base font-bold text-gray-800 mb-1.5">Strategic Reasoning</p>
              <p className="text-base text-gray-700 bg-gray-50 p-4 rounded-xl border border-gray-200 leading-relaxed font-normal">
                {recommendation.reasoning}
              </p>
            </div>
          </div>
        )}

        {!recLoading && !recError && !recommendation && (
          <p className="text-base text-gray-500 py-2">
            Submit offers via the Customer View to generate recommendations.
          </p>
        )}
      </div>

      {/* Offers */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-7 shadow-xs">
        <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900 mb-5">
          Customer Offers
          {offers && <span className="ml-2 text-gray-400 font-semibold text-base sm:text-lg">({offers.length})</span>}
        </h2>

        {offers && offers.length === 0 && (
          <p className="text-base text-gray-500 py-2">No offers received yet.</p>
        )}

        {offers && offers.length > 0 && (
          <div className="overflow-x-auto border border-gray-200 rounded-xl">
            <table className="w-full text-left border-collapse min-w-[650px]">
              <thead>
                <tr className="bg-gray-50/90 border-b border-gray-200 text-xs sm:text-sm font-bold text-gray-600 uppercase tracking-wider">
                  <th className="px-5 py-3.5">Customer</th>
                  <th className="px-4 py-3.5">Email</th>
                  <th className="px-4 py-3.5 text-right">Offered</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Time</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {offers.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="px-5 py-4 font-bold text-base text-gray-900">{o.customer_name}</td>
                    <td className="px-4 py-4 text-base text-gray-600">{o.customer_email}</td>
                    <td className="px-4 py-4 text-right font-mono font-extrabold text-lg sm:text-xl text-gray-900">₹{o.offered_price.toLocaleString()}</td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`inline-block px-3 py-1 text-xs sm:text-sm font-bold rounded-full ${OFFER_STATUS_COLORS[o.status] || "bg-gray-100 text-gray-600"}`}>
                        {o.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-gray-500 text-xs sm:text-sm whitespace-nowrap font-medium">{formatDate(o.created_at)}</td>
                    <td className="px-5 py-4 text-right whitespace-nowrap">
                      {bargain.status === "ACTIVE" && o.status === "PENDING" ? (
                        <div className="flex items-center justify-end gap-2.5">
                          <button
                            onClick={() => handleApprove(o.id)}
                            disabled={actionLoading !== null}
                            className="px-3.5 py-1.5 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 shadow-xs"
                          >
                            {actionLoading === o.id ? "…" : "Approve"}
                          </button>
                          <button
                            onClick={() => handleReject(o.id)}
                            disabled={actionLoading !== null}
                            className="px-3.5 py-1.5 bg-gray-100 text-gray-800 text-sm font-bold rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 border border-gray-200"
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-gray-300 text-sm font-semibold">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Log */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 sm:p-7 shadow-xs">
        <h2 className="text-xl sm:text-2xl font-extrabold text-gray-900 mb-5">
          Audit Log
          {audit && <span className="ml-2 text-gray-400 font-semibold text-base sm:text-lg">({audit.length})</span>}
        </h2>

        {audit && audit.length === 0 && (
          <p className="text-base text-gray-500 py-2">No audit entries.</p>
        )}

        {audit && audit.length > 0 && (
          <div className="space-y-3">
            {audit.map((a) => (
              <div key={a.id} className="flex items-start gap-4 text-base border-b border-gray-100 pb-3 last:border-b-0">
                <span className="text-xs sm:text-sm text-gray-500 font-mono whitespace-nowrap mt-0.5">{formatDate(a.created_at)}</span>
                <div>
                  <span className="font-bold text-gray-900">{a.event}</span>
                  {a.details && <p className="text-gray-600 mt-1 text-sm sm:text-base leading-relaxed">{a.details}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
