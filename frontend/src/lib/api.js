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



