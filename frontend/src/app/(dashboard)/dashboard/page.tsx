"use client";

import Image from "next/image";
import Link from "next/link";

import SimulatedBadge from "@/components/SimulatedBadge";
import TierChip from "@/components/TierChip";
import { formatIdr } from "@/lib/api";
import { useRecentTransactions } from "@/lib/data";
import { STR } from "@/lib/strings";

// Dashboard is English-only (still sourced from strings.ts).
const D = STR.dashboard;

export default function DashboardPage() {
  const { transactions, mode } = useRecentTransactions();

  // Display-only sums of engine numbers (R1: no client-side pricing).
  const totalKg = transactions.reduce((acc, tx) => acc + tx.weightKg, 0);
  const totalIdr = transactions.reduce((acc, tx) => acc + tx.totalIdr, 0);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-extrabold text-leaf">{STR.appName.en}</h1>
          <span className="text-xl font-semibold text-slate">{D.title.en}</span>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase ${
              mode === "firestore" ? "bg-leaf text-white" : "bg-slate/15 text-slate"
            }`}
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute h-2 w-2 animate-ping rounded-full bg-current opacity-60" />
              <span className="h-2 w-2 rounded-full bg-current" />
            </span>
            {mode === "firestore" ? D.modeLive.en : D.modePoll.en}
          </span>
          <Link href="/" className="text-sm font-semibold text-slate underline">
            Station
          </Link>
        </div>
      </header>

      {/* today's totals strip */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: D.txCount.en, value: String(transactions.length) },
          { label: D.totalKg.en, value: totalKg.toFixed(1) },
          { label: D.totalIdr.en, value: formatIdr(totalIdr) },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="rounded-3xl border border-slate/20 bg-white p-5"
          >
            <p className="text-sm font-semibold uppercase tracking-wide text-slate">
              {label}
            </p>
            <p className="mt-1 text-3xl font-extrabold tabular-nums">{value}</p>
          </div>
        ))}
      </section>

      {/* live feed */}
      <section className="rounded-3xl border border-slate/20 bg-white">
        <div className="flex items-center justify-between border-b border-slate/15 px-5 py-4">
          <h2 className="text-lg font-bold">{D.liveFeed.en}</h2>
        </div>
        {transactions.length === 0 ? (
          <p className="p-8 text-center text-slate">{D.empty.en}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate">
                <tr className="border-b border-slate/15">
                  <th className="px-5 py-3">{D.time.en}</th>
                  <th className="px-5 py-3">{D.farmer.en}</th>
                  <th className="px-5 py-3">{D.grade.en}</th>
                  <th className="px-5 py-3 text-right">{D.weight.en}</th>
                  <th className="px-5 py-3 text-right">{D.price.en}</th>
                  <th className="px-5 py-3 text-right">Total</th>
                  <th className="px-5 py-3">
                    <span className="flex items-center gap-2">
                      {D.payment.en} <SimulatedBadge />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.txId} className="border-b border-slate/10">
                    <td className="px-5 py-3 tabular-nums text-slate">
                      {new Date(tx.createdAt).toLocaleTimeString("en-GB")}
                    </td>
                    <td className="px-5 py-3 font-semibold">{tx.farmerName}</td>
                    <td className="px-5 py-3">
                      <TierChip tier={tx.tier} lang="en" />
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums">
                      {tx.weightKg.toFixed(2)} kg
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums">
                      {formatIdr(tx.pricePerKg)}
                    </td>
                    <td className="px-5 py-3 text-right font-bold tabular-nums">
                      {formatIdr(tx.totalIdr)}
                    </td>
                    <td className="px-5 py-3">
                      {tx.certId ? (
                        <Link
                          href={`/cert/${tx.certId}`}
                          className="font-mono text-xs text-leaf underline"
                        >
                          {tx.status}
                        </Link>
                      ) : (
                        <span className="font-mono text-xs">{tx.status}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* coop-as-community-channel strip */}
      <section className="grid grid-cols-3 gap-4">
        {[
          { src: "/images/intake-desk.png", alt: STR.images.intake.en },
          { src: "/images/coop-storefront.png", alt: STR.images.storefront.en },
          { src: "/images/hands-exchange.png", alt: STR.images.hands.en },
        ].map(({ src, alt }) => (
          <Image
            key={src}
            src={src}
            alt={alt}
            width={800}
            height={533}
            className="w-full rounded-2xl object-cover"
          />
        ))}
      </section>
      <p className="pb-4 text-center text-sm text-slate">{D.aboutStrip.en}</p>
    </main>
  );
}
