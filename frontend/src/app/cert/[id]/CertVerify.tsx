"use client";

import useSWR from "swr";

import SimulatedBadge from "@/components/SimulatedBadge";
import TierChip from "@/components/TierChip";
import { api, ApiError, formatIdr } from "@/lib/api";
import { STR } from "@/lib/strings";

const C = STR.cert;

/** Public verification page — what the QR on the printed certificate opens. */
export default function CertVerify({ certId }: { certId: string }) {
  const { data, error, isLoading } = useSWR(`cert-${certId}`, () =>
    api.certificate(certId, true),
  );

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-leaf">{STR.appName.id}</h1>
        <SimulatedBadge />
      </header>
      <div>
        <h2 className="text-3xl font-bold">{C.title.id}</h2>
        <p className="text-slate">{C.title.en}</p>
      </div>

      {isLoading ? (
        <p className="animate-pulse rounded-3xl bg-white p-8 text-center text-lg text-slate">
          {C.checking.id} / {C.checking.en}
        </p>
      ) : null}

      {error ? (
        <p className="rounded-3xl bg-terra/15 p-8 text-center text-lg font-semibold text-terra">
          {error instanceof ApiError && error.status === 404
            ? `${C.notFound.id} / ${C.notFound.en}`
            : `${STR.station.txFailed.id} / ${STR.station.txFailed.en}`}
        </p>
      ) : null}

      {data ? (
        <>
          <div
            className={`rounded-3xl p-6 text-white ${
              data.valid ? "bg-leaf" : "bg-terra"
            }`}
          >
            <p className="text-4xl font-extrabold">
              {data.valid ? C.valid.id : C.invalid.id}
              <span className="ml-3 text-xl font-semibold opacity-80">
                {data.valid ? C.valid.en : C.invalid.en}
              </span>
            </p>
            <p className="mt-1 opacity-90">
              {data.valid ? C.validSub.id : C.invalidSub.id}
            </p>
            <p className="text-sm opacity-75">
              {data.valid ? C.validSub.en : C.invalidSub.en}
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-4 rounded-3xl border border-slate/20 bg-white p-6">
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.farmer.id} / {C.farmer.en}
              </dt>
              <dd className="text-lg font-bold">{data.transaction.farmerName}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.grade.id} / {C.grade.en}
              </dt>
              <dd className="mt-1">
                <TierChip tier={data.transaction.tier} />
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.weight.id} / {C.weight.en}
              </dt>
              <dd className="text-lg font-bold tabular-nums">
                {data.transaction.weightKg} kg
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.total.id} / {C.total.en}
              </dt>
              <dd className="flex items-center gap-2 text-lg font-bold tabular-nums">
                {formatIdr(data.transaction.totalIdr)} <SimulatedBadge />
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.issuedAt.id} / {C.issuedAt.en}
              </dt>
              <dd className="font-medium">
                {new Date(data.transaction.createdAt).toLocaleString("id-ID")}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.location.id} / {C.location.en}
              </dt>
              <dd className="font-medium tabular-nums">
                {data.transaction.gps.lat.toFixed(5)},{" "}
                {data.transaction.gps.lng.toFixed(5)}
                <a
                  href={`https://www.openstreetmap.org/?mlat=${data.transaction.gps.lat}&mlon=${data.transaction.gps.lng}#map=17/${data.transaction.gps.lat}/${data.transaction.gps.lng}`}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-2 text-leaf underline"
                >
                  {C.viewMap.id}
                </a>
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="text-xs font-semibold uppercase text-slate">
                {C.hashLabel.id} / {C.hashLabel.en}
              </dt>
              <dd className="break-all font-mono text-xs text-slate">
                {data.certificate.sha256}
              </dd>
            </div>
          </dl>
        </>
      ) : null}
    </main>
  );
}
