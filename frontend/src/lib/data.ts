"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";

import { api, Transaction } from "./api";

export type DataMode = "poll" | "firestore";

export const DATA_MODE: DataMode =
  process.env.NEXT_PUBLIC_DATA_MODE === "firestore" ? "firestore" : "poll";

export function useRecentTransactions(): {
  transactions: Transaction[];
  mode: DataMode;
} {
  const poll = useSWR(
    DATA_MODE === "poll" ? "recent-transactions" : null,
    () => api.recentTransactions().then((r) => r.transactions),

    { refreshInterval: 2000, refreshWhenHidden: true },
  );

  const [snapshot, setSnapshot] = useState<Transaction[]>([]);
  useEffect(() => {
    if (DATA_MODE !== "firestore") return;
    let unsubscribe: (() => void) | undefined;
    let cancelled = false;
    (async () => {
      const { getDb } = await import("./firebase");
      const { collection, limit, onSnapshot, orderBy, query } = await import(
        "firebase/firestore"
      );
      if (cancelled) return;
      const q = query(
        collection(getDb(), "transactions"),
        orderBy("createdAt", "desc"),
        limit(25),
      );
      unsubscribe = onSnapshot(q, (snap) =>
        setSnapshot(snap.docs.map((doc) => doc.data() as Transaction)),
      );
    })();
    return () => {
      cancelled = true;
      unsubscribe?.();
    };
  }, []);

  if (DATA_MODE === "firestore") {
    return { transactions: snapshot, mode: "firestore" };
  }
  return { transactions: poll.data ?? [], mode: "poll" };
}
