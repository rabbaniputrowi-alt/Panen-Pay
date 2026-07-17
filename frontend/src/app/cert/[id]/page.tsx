import CertVerify from "./CertVerify";

export default async function CertPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CertVerify certId={id} />;
}
