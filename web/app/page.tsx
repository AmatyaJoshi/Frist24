import { getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  const health = await getHealth();
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold">CRA Article 14, without the panic.</h1>
      <p style={{ color: "var(--muted)" }} className="max-w-2xl">
        Frist24 watches your SBOMs against CISA KEV, FIRST EPSS and OSV.dev, opens an incident the
        moment a component is listed as actively exploited, and starts the 24h / 72h / 14d clock. A
        local model drafts the ENISA reports. You approve. Everything is logged in a hash-chained
        audit trail. No vulnerability data leaves this machine.
      </p>
      <section className="rounded-lg border border-white/10 p-4 text-sm font-mono">
        <div>api: {health ? health.status : "unreachable"}</div>
        <div>db: {health?.db ?? "-"}</div>
        <div>
          ollama: {health?.ollama.status ?? "-"}{" "}
          {health?.ollama.models?.length ? `(${health.ollama.models.join(", ")})` : "(no models yet)"}
        </div>
      </section>
    </div>
  );
}
