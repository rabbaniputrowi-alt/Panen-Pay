"use client";

import Image from "next/image";
import Link from "next/link";
import { useRef, useState } from "react";

import CertificateQR from "@/components/CertificateQR";
import GradeCard from "@/components/GradeCard";
import SimulatedBadge from "@/components/SimulatedBadge";
import WeightLive from "@/components/WeightLive";
import {
  api,
  formatIdr,
  GPS,
  GradeResult,
  TransactionResponse,
} from "@/lib/api";
import { STR } from "@/lib/strings";

type Step = "photo" | "grade" | "weigh" | "done";

const STEPS: Step[] = ["photo", "grade", "weigh", "done"];
const STEP_TITLES = {
  photo: STR.station.stepPhoto,
  grade: STR.station.stepGrade,
  weigh: STR.station.stepWeigh,
  done: STR.station.stepDone,
};
const FALLBACK_GPS: GPS = { lat: -7.797068, lng: 110.370529 };

function currentGps(): Promise<GPS> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(FALLBACK_GPS);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(FALLBACK_GPS),
      { timeout: 3000 },
    );
  });
}

export default function StationPage() {
  const [step, setStep] = useState<Step>("photo");
  const [photoUrl, setPhotoUrl] = useState<string>();
  const [grade, setGrade] = useState<GradeResult>();
  const [farmerName, setFarmerName] = useState("");
  const [result, setResult] = useState<TransactionResponse>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const fileInput = useRef<HTMLInputElement>(null);

  async function handlePhoto(file: File) {
    setError(undefined);
    setBusy(true);
    const url = URL.createObjectURL(file);
    setPhotoUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return url;
    });
    try {
      setGrade(await api.gradePhoto(file, file.name || "photo.jpg"));
      setStep("grade");
    } catch {
      setError(`${STR.station.gradeFailed.id} / ${STR.station.gradeFailed.en}`);
    } finally {
      setBusy(false);
    }
  }

  async function confirmTransaction() {
    setError(undefined);
    setBusy(true);
    try {
      const gps = await currentGps();
      setResult(await api.createTransaction(farmerName.trim(), gps));
      setStep("done");
    } catch {
      setError(`${STR.station.txFailed.id} / ${STR.station.txFailed.en}`);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    setPhotoUrl(undefined);
    setGrade(undefined);
    setFarmerName("");
    setResult(undefined);
    setError(undefined);
    setStep("photo");
  }

  const retake = () => {
    setGrade(undefined);
    setStep("photo");
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-leaf">{STR.appName.id}</h1>
        <Link
          href="/dashboard"
          className="-mr-2 flex min-h-11 items-center px-2 text-sm font-semibold text-slate underline"
        >
          {STR.dashboard.title.id}
        </Link>
      </header>

      <ol className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <li
            key={s}
            className={`h-2 flex-1 rounded-full ${
              STEPS.indexOf(step) >= i ? "bg-leaf" : "bg-slate/20"
            }`}
          />
        ))}
      </ol>

      <div>
        <h2 className="text-3xl font-bold">{STEP_TITLES[step].id}</h2>
        <p className="text-slate">{STEP_TITLES[step].en}</p>
      </div>

      {error ? (
        <p className="rounded-2xl bg-terra/15 p-4 font-semibold text-terra">{error}</p>
      ) : null}

      {step === "photo" ? (
        <section className="flex flex-col gap-6">
          <Image
            src="/images/hero-farmer.png"
            alt={STR.images.hero.id}
            width={1200}
            height={800}
            priority
            className="w-full rounded-3xl object-cover"
          />
          <input
            ref={fileInput}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handlePhoto(file);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            disabled={busy}
            onClick={() => fileInput.current?.click()}
            className="min-h-20 rounded-3xl bg-leaf px-6 text-2xl font-bold text-white transition-colors hover:bg-leaf/90 disabled:opacity-60"
          >
            {busy ? STR.station.grading.id : STR.station.takePhoto.id}
            <span className="block text-base font-medium opacity-80">
              {busy ? STR.station.grading.en : STR.station.takePhoto.en}
            </span>
          </button>
        </section>
      ) : null}

      {step === "grade" && grade ? (
        <section className="flex flex-col gap-6">
          <GradeCard grade={grade} photoUrl={photoUrl} onRetake={retake} />
          <button
            type="button"
            onClick={() => setStep("weigh")}
            className="min-h-20 rounded-3xl bg-leaf px-6 text-2xl font-bold text-white hover:bg-leaf/90"
          >
            {STR.station.continueToWeigh.id}
            <span className="block text-base font-medium opacity-80">
              {STR.station.continueToWeigh.en}
            </span>
          </button>
        </section>
      ) : null}

      {step === "weigh" && grade ? (
        <section className="flex flex-col gap-6">
          <WeightLive />
          <label className="flex flex-col gap-2 text-lg font-semibold">
            {STR.station.farmerName.id}
            <span className="text-sm font-normal text-slate">
              {STR.station.farmerName.en}
            </span>
            <input
              value={farmerName}
              onChange={(e) => setFarmerName(e.target.value)}
              placeholder={STR.station.farmerNamePlaceholder.id}
              className="min-h-16 rounded-2xl border-2 border-slate/30 bg-white px-4 text-xl focus:border-leaf focus:outline-none"
            />
          </label>
          <button
            type="button"
            disabled={busy || farmerName.trim() === ""}
            onClick={() => void confirmTransaction()}
            className="min-h-20 rounded-3xl bg-leaf px-6 text-2xl font-bold text-white hover:bg-leaf/90 disabled:opacity-50"
          >
            {busy ? STR.station.submitting.id : STR.station.confirm.id}
            <span className="block text-base font-medium opacity-80">
              {busy ? STR.station.submitting.en : STR.station.confirm.en}
            </span>
          </button>
        </section>
      ) : null}

      {step === "done" && result ? (
        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between rounded-3xl bg-leaf p-6 text-white">
            <div>
              <p className="text-sm font-semibold uppercase opacity-80">
                {STR.station.total.id} / {STR.station.total.en}
              </p>
              <p className="text-4xl font-extrabold">
                {formatIdr(result.transaction.totalIdr)}
              </p>
              <p className="opacity-80">
                {result.transaction.weightKg} kg ×{" "}
                {formatIdr(result.transaction.pricePerKg)}/kg
              </p>
            </div>
            <SimulatedBadge />
          </div>
          <CertificateQR
            certificate={result.certificate}
            gps={result.transaction.gps}
          />
          <p className="rounded-2xl bg-white p-4 text-sm leading-relaxed text-slate">
            <span className="font-semibold">
              {STR.station.brief.id} / {STR.station.brief.en}:
            </span>{" "}
            {result.brief}
          </p>
          <button
            type="button"
            onClick={reset}
            className="min-h-20 rounded-3xl border-2 border-leaf px-6 text-2xl font-bold text-leaf hover:bg-leaf/10"
          >
            {STR.station.newTransaction.id}
            <span className="block text-base font-medium opacity-70">
              {STR.station.newTransaction.en}
            </span>
          </button>
        </section>
      ) : null}
    </main>
  );
}
