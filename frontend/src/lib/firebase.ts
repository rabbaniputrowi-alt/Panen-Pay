/**
 * Firebase web client config — real project `test-970e2`, public by design
 * (§E). Used ONLY when NEXT_PUBLIC_DATA_MODE=firestore, and only for reads:
 * clients never write to the database (R2). No Analytics — it breaks SSR and
 * is unused.
 */

import { getApps, initializeApp } from "firebase/app";
import { Firestore, getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAN5BY4ynwE9oELdAfYHOR2O-r0ztn_cKE",
  authDomain: "test-970e2.firebaseapp.com",
  projectId: "test-970e2",
  storageBucket: "test-970e2.firebasestorage.app",
  messagingSenderId: "403729442816",
  appId: "1:403729442816:web:74ac58ed86a0b7558850e5",
};

export function getDb(): Firestore {
  const app = getApps()[0] ?? initializeApp(firebaseConfig);
  return getFirestore(app);
}
