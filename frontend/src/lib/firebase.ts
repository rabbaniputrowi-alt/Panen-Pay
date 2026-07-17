

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
