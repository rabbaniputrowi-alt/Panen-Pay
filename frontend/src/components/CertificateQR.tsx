import { Certificate, GPS } from "@/lib/api";
import { STR } from "@/lib/strings";

export default function CertificateQR({
  certificate,
  gps,
}: {
  certificate: Certificate;
  gps?: GPS;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-3xl border border-slate/20 bg-white p-6">
      {certificate.qrPngDataUri ? (
        // base64 data URI issued by the server — next/image can't optimize it
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={certificate.qrPngDataUri}
          alt={STR.station.scanHint.id}
          className="h-52 w-52"
        />
      ) : (
        <a className="text-leaf underline" href={certificate.qrPayloadUrl}>
          {certificate.qrPayloadUrl}
        </a>
      )}
      <p className="text-center text-sm text-slate">
        {STR.station.scanHint.id}
        <span className="block text-xs">{STR.station.scanHint.en}</span>
      </p>
      <dl className="w-full space-y-1 border-t border-slate/15 pt-3 font-mono text-xs text-slate">
        <div className="flex justify-between gap-2">
          <dt>{STR.cert.hashLabel.en}</dt>
          <dd title={certificate.sha256}>{certificate.sha256.slice(0, 12)}…</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>{STR.cert.issuedAt.en}</dt>
          <dd>{new Date(certificate.issuedAt).toLocaleString("id-ID")}</dd>
        </div>
        {gps ? (
          <div className="flex justify-between gap-2">
            <dt>{STR.cert.location.en}</dt>
            <dd>
              {gps.lat.toFixed(5)}, {gps.lng.toFixed(5)}
            </dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
