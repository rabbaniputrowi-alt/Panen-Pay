import { STR } from "@/lib/strings";

/** R3: every payment surface renders this badge. Slate pill, locked copy. */
export default function SimulatedBadge() {
  return (
    <span className="inline-flex items-center rounded-full bg-slate px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-white">
      {STR.simulated.id} · {STR.simulated.en}
    </span>
  );
}
