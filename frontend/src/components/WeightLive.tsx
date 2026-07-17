"use client";

import useSWR from "swr";

import { api } from "@/lib/api";
import { STR } from "@/lib/strings";

export default function WeightLive() {
  const { data } = useSWR("station-state", () => api.stationState(), {
    refreshInterval: 1000,

    refreshWhenHidden: true,
  });
  const state = data?.state;
  const kg = (state?.lastWeightGrams ?? 0) / 1000;
  const stable = state?.stable ?? false;

  return (
    <div
      className={`flex flex-col items-center gap-2 rounded-3xl border-2 bg-white p-8 transition-all ${
        stable ? "border-leaf ring-4 ring-leaf/30" : "border-slate/20 animate-pulse"
      }`}
    >
      <div className="flex items-baseline gap-2">
        <span className="text-7xl font-extrabold tabular-nums tracking-tight">
          {kg.toFixed(2)}
        </span>
        <span className="text-3xl font-semibold text-slate">kg</span>
      </div>
      <p className={`text-lg font-semibold ${stable ? "text-leaf" : "text-slate"}`}>
        {stable ? STR.station.stable.id : STR.station.waitingStable.id}
      </p>
      <p className="text-sm text-slate">
        {stable ? STR.station.stable.en : STR.station.waitingStable.en}
      </p>
    </div>
  );
}
