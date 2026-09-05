const API_BASE = "http://127.0.0.1:8000";

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message =
      data && typeof data === "object" && data.detail
        ? typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail)
        : `Request failed (${res.status})`;
    throw new Error(message);
  }

  return data;
}

export function getBargains() {
  return apiFetch("/bargains/");
}

export function getBargain(id) {
  return apiFetch(`/bargains/${id}`);
}

export function getProducts() {
  return apiFetch("/products/");
}

export function createProduct(body) {
  return apiFetch("/products/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}


export function createBargain(body) {
  return apiFetch("/bargains/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getOffers(bargainId) {
  return apiFetch(`/bargains/${bargainId}/offers`);
}

export function createOffer(bargainId, body) {
  return apiFetch(`/bargains/${bargainId}/offers`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getAuditLog(bargainId) {
  return apiFetch(`/bargains/${bargainId}/audit`);
}

export function getRecommendation(bargainId) {
  return apiFetch(`/bargains/${bargainId}/recommendation`);
}

export function approveOffer(bargainId, offerId) {
  return apiFetch(`/bargains/${bargainId}/approve`, {
    method: "POST",
    body: JSON.stringify({ offer_id: offerId }),
  });
}

export function rejectOffer(bargainId, offerId) {
  return apiFetch(`/bargains/${bargainId}/reject`, {
    method: "POST",
    body: JSON.stringify({ offer_id: offerId }),
  });
}

export function createPaymentOrder(bargainId, offerId) {
  return apiFetch("/payments/create-order", {
    method: "POST",
    body: JSON.stringify({ bargain_id: bargainId, offer_id: offerId }),
  });
}

// ── MerchantIQ AI Endpoints (Phases 2-4) ──────────────────────

export function getDiscoveries() {
  return apiFetch("/ai/discoveries");
}

export function getDiscovery(discoveryId) {
  return apiFetch(`/ai/discoveries/${discoveryId}`);
}

export function investigateDiscovery(discoveryId) {
  return apiFetch(`/ai/investigate/${discoveryId}`, {
    method: "POST",
  });
}

export function getInvestigations() {
  return apiFetch("/ai/investigations");
}

export function resolveDiscovery(discoveryId) {
  return apiFetch(`/ai/resolve/${discoveryId}`, {
    method: "POST",
  });
}

export function getResolutions() {
  return apiFetch("/ai/resolutions");
}

export function getResolution(resolutionId) {
  return apiFetch(`/ai/resolutions/${resolutionId}`);
}

export async function analyzeMerchantCsv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("http://127.0.0.1:8000/ai/analyze-csv", {
    method: "POST",
    body: formData,
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || "Failed to analyze merchant CSV file.";
    const err = new Error(message);
    err.details = detail;
    throw err;
  }

  return data;
}

export function resetDemoDataset() {
  return apiFetch("/ai/reset-demo", {
    method: "POST",
  });
}

export function getDatasetInfo() {
  return apiFetch("/ai/dataset-info");
}
