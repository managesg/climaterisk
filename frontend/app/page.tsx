import Link from "next/link";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-blue-900 text-white">
      <div className="max-w-5xl mx-auto px-6 py-16">
        <h1 className="text-4xl font-bold mb-2">SeaBridge AI Sustainability Toolkit</h1>
        <p className="text-blue-200 text-lg mb-12">
          Physical climate risk · Transition risk · Nature risk · ISSB IFRS S2 / TCFD / TNFD disclosure
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <NavCard
            href="/properties"
            title="🏢 Properties"
            description="Manage your asset portfolio. Add buildings and run physical risk assessments."
          />
          <NavCard
            href="/agent"
            title="🤖 AI Agent"
            description="Run the full LangGraph assessment workflow: physical risk, transition risk, opportunities, and disclosure."
          />
          <NavCard
            href="/assessment"
            title="📊 Risk Scorecards"
            description="View hazard-by-hazard risk scores with feature drill-down and data source citations."
          />
          <NavCard
            href="/disclosure"
            title="📄 Disclosure"
            description="Generate ISSB IFRS S2 / TCFD / TNFD-aligned disclosure reports with full source attribution."
          />
        </div>

        <div className="mt-12 p-4 bg-white/10 rounded-lg border border-white/20 text-sm text-blue-100">
          <strong>Data integrity:</strong> All outputs distinguish observed data, modelled data,
          scenario assumptions, AI-generated interpretation, user-provided information, and missing data.
          No financial figures are fabricated. Every claim is sourced.
        </div>
      </div>
    </main>
  );
}

function NavCard({ href, title, description }: { href: string; title: string; description: string }) {
  return (
    <Link
      href={href}
      className="block p-6 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl transition-colors"
    >
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-blue-100 text-sm">{description}</p>
    </Link>
  );
}
