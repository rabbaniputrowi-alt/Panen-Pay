

export interface LStr {
  id: string;
  en: string;
}

export const STR = {
  appName: { id: "Panen Pay", en: "Panen Pay" },
  tagline: {
    id: "Lapisan bukti di meja setor cabai koperasi",
    en: "The evidence layer at the cooperative's chili intake desk",
  },
  simulated: { id: "SIMULASI", en: "SIMULATED" },

  tier: {
    fresh: { id: "Segar", en: "Fresh" },
    sell_today: { id: "Jual Hari Ini", en: "Sell Today" },
    wilted: { id: "Layu", en: "Wilted" },
  } as Record<string, LStr>,

  confidence: {
    high: { id: "Keyakinan tinggi", en: "High confidence" },
    medium: { id: "Keyakinan sedang", en: "Medium confidence" },
    low: { id: "Keyakinan rendah", en: "Low confidence" },
  } as Record<string, LStr>,

  station: {
    stepPhoto: { id: "Foto Panen", en: "Photograph the harvest" },
    stepGrade: { id: "Hasil Penilaian", en: "Grade result" },
    stepWeigh: { id: "Timbang & Data Petani", en: "Weigh & farmer details" },
    stepDone: { id: "Sertifikat Terbit", en: "Certificate issued" },
    takePhoto: { id: "Ambil / Unggah Foto", en: "Take or upload a photo" },
    grading: { id: "Menilai foto…", en: "Grading photo…" },
    gradeFailed: {
      id: "Penilaian gagal, coba lagi",
      en: "Grading failed — try again",
    },
    retake: { id: "Ambil Ulang Foto", en: "Retake photo" },
    lowConfidenceHint: {
      id: "Keyakinan rendah — sebaiknya foto ulang",
      en: "Low confidence — a retake is recommended",
    },
    continueToWeigh: { id: "Lanjut Timbang", en: "Continue to weighing" },
    farmerName: { id: "Nama Petani", en: "Farmer name" },
    farmerNamePlaceholder: { id: "cth. Bu Sari", en: "e.g. Bu Sari" },
    waitingStable: {
      id: "Menunggu timbangan stabil…",
      en: "Waiting for a stable weight…",
    },
    stable: { id: "Stabil", en: "Stable" },
    confirm: { id: "Konfirmasi Transaksi", en: "Confirm transaction" },
    submitting: { id: "Menyimpan…", en: "Saving…" },
    txFailed: {
      id: "Transaksi gagal — periksa timbangan dan foto",
      en: "Transaction failed — check the scale and photo",
    },
    total: { id: "Total Pembayaran", en: "Total payout" },
    brief: { id: "Ringkasan", en: "Brief" },
    newTransaction: { id: "Transaksi Baru", en: "New transaction" },
    scanHint: {
      id: "Pindai QR untuk memverifikasi sertifikat",
      en: "Scan the QR to verify the certificate",
    },
  },

  dashboard: {
    title: { id: "Dasbor Koperasi", en: "Cooperative Dashboard" },
    liveFeed: { id: "Setoran terbaru", en: "Live intake feed" },
    txCount: { id: "Transaksi hari ini", en: "Transactions" },
    totalKg: { id: "Total berat (kg)", en: "Total weight (kg)" },
    totalIdr: { id: "Total pembayaran (IDR)", en: "Total payout (IDR)" },
    time: { id: "Waktu", en: "Time" },
    farmer: { id: "Petani", en: "Farmer" },
    grade: { id: "Grade", en: "Grade" },
    weight: { id: "Berat", en: "Weight" },
    price: { id: "Harga/kg", en: "Price/kg" },
    payment: { id: "Pembayaran", en: "Payment" },
    modePoll: { id: "polling 2 dtk", en: "2s polling" },
    modeLive: { id: "langsung", en: "live" },
    empty: {
      id: "Belum ada transaksi — jalankan simulator atau stasiun.",
      en: "No transactions yet — run the simulator or the station.",
    },
    aboutStrip: {
      id: "Koperasi sebagai saluran komunitas",
      en: "The cooperative as the community channel",
    },
  },

  cert: {
    title: { id: "Sertifikat Panen", en: "Harvest Certificate" },
    checking: { id: "Memeriksa keaslian…", en: "Verifying…" },
    valid: { id: "VALID", en: "VALID" },
    invalid: { id: "TIDAK VALID", en: "INVALID" },
    validSub: {
      id: "Hash cocok — data transaksi tidak diubah",
      en: "Hash matches — the record is untampered",
    },
    invalidSub: {
      id: "Hash tidak cocok — data telah berubah",
      en: "Hash mismatch — the record was altered",
    },
    notFound: {
      id: "Sertifikat tidak ditemukan",
      en: "Certificate not found",
    },
    farmer: { id: "Petani", en: "Farmer" },
    grade: { id: "Grade", en: "Grade" },
    weight: { id: "Berat", en: "Weight" },
    total: { id: "Total", en: "Total" },
    issuedAt: { id: "Diterbitkan", en: "Issued" },
    location: { id: "Lokasi", en: "Location" },
    viewMap: { id: "Lihat peta", en: "View map" },
    hashLabel: { id: "Sidik jari SHA-256", en: "SHA-256 fingerprint" },
  },

  images: {
    hero: {
      id: "Petani memegang cabai merah hasil panen",
      en: "Farmer holding freshly harvested red chilies",
    },
    intake: {
      id: "Penimbangan di meja setor koperasi",
      en: "Weighing at the cooperative intake desk",
    },
    storefront: { id: "Depan kios koperasi", en: "Cooperative storefront" },
    hands: {
      id: "Tangan bertukar hasil panen",
      en: "Hands exchanging produce",
    },
  },
} as const;
