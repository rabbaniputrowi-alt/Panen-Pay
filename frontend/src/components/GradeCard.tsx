"use client";

import { GradeResult } from "@/lib/api";
import { STR } from "@/lib/strings";
import TierChip from "./TierChip";

export default function GradeCard({
  grade,
  photoUrl,
  onRetake,
}: {
  grade: GradeResult;
  photoUrl?: string;
  onRetake?: () => void;
}) {
  const lowConfidence = grade.confidence === "low";
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate/20 bg-white p-6">
      <div className="flex items-center gap-4">
        {photoUrl ? (

          <img
            src={photoUrl}
            alt={STR.images.hero.id}
            className="h-24 w-24 rounded-2xl object-cover"
          />
        ) : null}
        <div className="flex flex-col gap-2">
          <TierChip tier={grade.grade} />
          <p className="text-sm font-medium text-slate">
            {STR.confidence[grade.confidence].id}
            <span className="block text-xs">{STR.confidence[grade.confidence].en}</span>
          </p>
        </div>
      </div>
      <p className="text-base leading-relaxed">{grade.visual_evidence}</p>
      {lowConfidence ? (
        <p className="rounded-xl bg-gold/20 p-3 text-sm font-semibold text-[#7a5c0a]">
          {STR.station.lowConfidenceHint.id}
          <span className="block font-normal">{STR.station.lowConfidenceHint.en}</span>
        </p>
      ) : null}
      {onRetake ? (
        <button
          type="button"
          onClick={onRetake}
          className={`min-h-14 rounded-2xl px-6 text-lg font-semibold transition-colors ${
            lowConfidence
              ? "bg-terra text-white hover:bg-terra/90"
              : "border-2 border-slate/30 text-slate hover:bg-slate/10"
          }`}
        >
          {STR.station.retake.id} / {STR.station.retake.en}
        </button>
      ) : null}
    </div>
  );
}
