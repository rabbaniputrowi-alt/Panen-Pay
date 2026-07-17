/** Typed fetch wrappers for every Phase-4 backend endpoint. */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Tier = "fresh" | "sell_today" | "wilted";
export type Confidence = "high" | "medium" | "low";

export interface GPS {
  lat: number;
  lng: number;
}

export interface GradeResult {
  grade: Tier;
  confidence: Confidence;
  visual_evidence: string;
}

export interface Transaction {
  txId: string;
  farmerName: string;
  tier: Tier;
  weightKg: number;
  pricePerKg: number;
  totalIdr: number;
  gps: GPS;
  createdAt: string;
  certificateHash: string;
  certId?: string;
  status: string;
  paidAt?: string;
}

export interface Certificate {
  certId: string;
  txId: string;
  sha256: string;
  qrPayloadUrl: string;
  issuedAt: string;
  qrPngDataUri?: string;
}

export interface StationState {
  stationId?: string;
  lastWeightGrams: number;
  stable: boolean;
  lastTier?: Tier | null;
  pendingGrade?: GradeResult | null;
  updatedAt: string;
}

export interface TransactionResponse {
  transaction: Transaction;
  certificate: Certificate;
  brief: string;
}

export interface CertificateResponse {
  certificate: Certificate;
  transaction: Transaction;
  valid?: boolean;
}

export interface Health {
  ok: boolean;
  grader: "mock" | "openai";
  store: "memory" | "firestore";
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return (await res.json()) as T;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const api = {
  health: () => request<Health>("/healthz"),

  ingestWeight: (weightGrams: number, stable: boolean, stationId = "station-1") =>
    postJson<{ ok: boolean }>("/api/v1/ingest/weight", {
      station_id: stationId,
      weight_grams: weightGrams,
      stable,
    }),

  gradePhoto: (photo: Blob, filename = "photo.jpg") => {
    const form = new FormData();
    form.append("photo", photo, filename);
    return request<GradeResult>("/api/v1/grade", { method: "POST", body: form });
  },

  createTransaction: (farmerName: string, gps: GPS, stationId = "station-1") =>
    postJson<TransactionResponse>("/api/v1/transactions", {
      farmerName,
      gps,
      stationId,
    }),

  recentTransactions: () =>
    request<{ transactions: Transaction[] }>("/api/v1/transactions/recent"),

  certificate: (certId: string, verify = true) =>
    request<CertificateResponse>(
      `/api/v1/certificates/${encodeURIComponent(certId)}${verify ? "?verify=1" : ""}`,
    ),

  stationState: () =>
    request<{ state: StationState | null }>("/api/v1/station/state"),

  stationFeedback: (stationId = "station-1") =>
    request<{ tone: string }>(
      `/api/v1/station/feedback?station_id=${encodeURIComponent(stationId)}`,
    ),
};

export function formatIdr(n: number): string {
  return `Rp${new Intl.NumberFormat("id-ID").format(n)}`;
}
