import { Tier } from "@/lib/api";
import { STR } from "@/lib/strings";

const TIER_CLASS: Record<Tier, string> = {
  fresh: "bg-leaf text-white",
  sell_today: "bg-gold text-[#4a3a08]",
  wilted: "bg-terra text-white",
};

export default function TierChip({
  tier,
  lang = "id",
}: {
  tier: Tier;
  lang?: "id" | "en";
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${TIER_CLASS[tier]}`}
    >
      {STR.tier[tier][lang]}
    </span>
  );
}
