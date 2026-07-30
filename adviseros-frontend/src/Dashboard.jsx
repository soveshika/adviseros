import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000/api/v1";

// ── Utilities ─────────────────────────────────────────────────────────────────
const timeAgo = (dateStr) => {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const riskColour = (r) => ({
  conservative: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
  moderate:     "bg-amber-900/40 text-amber-300 border-amber-700",
  aggressive:   "bg-red-900/40 text-red-300 border-red-700",
}[r] || "bg-slate-800 text-slate-300 border-slate-600");

const activityIcon = (title) => {
  if (title?.includes("Analysis")) return "🤖";
  if (title?.includes("Email"))    return "✉️";
  if (title?.includes("PDF") || title?.includes("Report")) return "📄";
  return "📋";
};

// ── Spinner ───────────────────────────────────────────────────────────────────
const Spinner = () => (
  <div className="flex items-center justify-center p-8">
    <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
  </div>
);

// ── Modal ─────────────────────────────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h3 className="text-white font-semibold text-lg" style={{ fontFamily: "Georgia, serif" }}>{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-2xl leading-none transition-colors">×</button>
        </div>
        <div className="overflow-y-auto flex-1 p-6">{children}</div>
      </div>
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon, sub }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 flex items-start gap-4">
      <div className="w-11 h-11 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-xl shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white" style={{ fontFamily: "Georgia, serif" }}>{value}</p>
        <p className="text-xs text-slate-400 uppercase tracking-widest mt-0.5">{label}</p>
        {sub && <p className="text-xs text-amber-400 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

// ── Action Button ─────────────────────────────────────────────────────────────
function ActionBtn({ onClick, loading, colour, children }) {
  const base = "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-50 border";
  const cols = {
    amber:   "border-amber-600/40 text-amber-300 hover:bg-amber-400/10",
    blue:    "border-blue-600/40 text-blue-300 hover:bg-blue-400/10",
    emerald: "border-emerald-600/40 text-emerald-300 hover:bg-emerald-400/10",
    violet:  "border-violet-600/40 text-violet-300 hover:bg-violet-400/10",
  };
  return (
    <button onClick={onClick} disabled={loading} className={`${base} ${cols[colour]}`}>
      {loading ? "…" : children}
    </button>
  );
}

// ── Profile Modal Content ─────────────────────────────────────────────────────
function ProfileContent({ client }) {
  const rows = [
    ["Full Name",   `${client.first_name} ${client.last_name}`],
    ["Email",       client.email],
    ["Risk Profile",client.risk_profile],
    ["Annual Income", client.annual_income ? `£${Number(client.annual_income).toLocaleString("en-GB")}` : "—"],
    ["Net Worth",   client.net_worth ? `£${Number(client.net_worth).toLocaleString("en-GB")}` : "—"],
    ["Investment Horizon", client.investment_horizon_years ? `${client.investment_horizon_years} years` : "—"],
    ["Status",      client.is_active ? "Active" : "Inactive"],
    ["Notes",       client.notes || "—"],
  ];
  return (
    <div className="space-y-2">
      {rows.map(([k, v]) => (
        <div key={k} className="flex gap-3 py-2 border-b border-slate-800">
          <span className="text-slate-400 text-sm w-40 shrink-0">{k}</span>
          <span className="text-white text-sm">{v}</span>
        </div>
      ))}
    </div>
  );
}

// ── Email Modal Content ───────────────────────────────────────────────────────
function EmailContent({ email }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(email);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div>
      <button onClick={copy} className="mb-4 px-4 py-2 bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs font-semibold rounded-lg hover:bg-amber-400/20 transition-all">
        {copied ? "✓ Copied!" : "Copy to Clipboard"}
      </button>
      <pre className="whitespace-pre-wrap text-slate-300 text-sm leading-relaxed font-mono bg-slate-800/60 rounded-xl p-4 border border-slate-700">
        {email}
      </pre>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard({ onNewClient }) {
  const [clients,    setClients]    = useState([]);
  const [reports,    setReports]    = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [modal,      setModal]      = useState(null); // { type, client, data }
  const [actionLoad, setActionLoad] = useState({}); // { clientId_action: true }
  const [toast,      setToast]      = useState(null);

  const showToast = (msg, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const setAL = (id, action, val) =>
    setActionLoad((p) => ({ ...p, [`${id}_${action}`]: val }));

  // Fetch all data
  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cr, rr] = await Promise.all([
        fetch(`${API}/clients?limit=100`),
        fetch(`${API}/reports?limit=20`),
      ]);
      if (cr.ok) setClients(await cr.json());
      if (rr.ok) setReports(await rr.json());
    } catch { /* network error */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── Actions ──────────────────────────────────────────────────────────────
  const runAnalysis = async (client) => {
    setAL(client.id, "analyse", true);
    try {
      const res = await fetch(`${API}/analyse/${client.id}`, { method: "POST" });
      if (res.ok) {
        showToast(`✓ Analysis complete for ${client.first_name}`);
        fetchAll();
      } else {
        showToast("Analysis failed — try again", false);
      }
    } catch { showToast("Network error", false); }
    setAL(client.id, "analyse", false);
  };

  const downloadPDF = async (client) => {
    setAL(client.id, "pdf", true);
    try {
      const res = await fetch(`${API}/report/${client.id}/pdf`);
      if (res.ok) {
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href     = url;
        a.download = `report_${client.id}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        showToast(`✓ PDF downloaded for ${client.first_name}`);
      } else {
        showToast("Run analysis first, then download PDF", false);
      }
    } catch { showToast("Network error", false); }
    setAL(client.id, "pdf", false);
  };

  const viewEmail = async (client) => {
    setAL(client.id, "email", true);
    try {
      const res = await fetch(`${API}/report/${client.id}/email`);
      if (res.ok) {
        const data = await res.json();
        setModal({ type: "email", client, data: data.email_draft });
      } else {
        showToast("Run analysis first, then view email", false);
      }
    } catch { showToast("Network error", false); }
    setAL(client.id, "email", false);
  };

  // ── Stats ─────────────────────────────────────────────────────────────────
  const totalClients   = clients.length;
  const totalReports   = reports.filter(r => r.generated_by?.startsWith("Mock/")).length;
  const activeClients  = clients.filter(c => c.is_active).length;

  // ── Recent activity ───────────────────────────────────────────────────────
  const activity = [...reports]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 10);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 flex" style={{ fontFamily: "Georgia, serif" }}>

      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-400 flex items-center justify-center">
              <span className="text-slate-950 font-bold text-sm">A</span>
            </div>
            <span className="text-white font-semibold tracking-wide">AdviserOS</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {[
            { icon: "⊞", label: "Dashboard",   active: true  },
            { icon: "👥", label: "Clients",     active: false },
            { icon: "📊", label: "Reports",     active: false },
            { icon: "🤖", label: "AI Analysis", active: false },
            { icon: "⚙️", label: "Settings",    active: false },
          ].map(({ icon, label, active }) => (
            <button key={label} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
              active
                ? "bg-amber-400/10 text-amber-300 border border-amber-400/20"
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            }`}>
              <span>{icon}</span>{label}
            </button>
          ))}
        </nav>

        {/* Adviser badge */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-amber-400/20 border border-amber-400/30 flex items-center justify-center text-amber-300 text-xs font-bold">JA</div>
            <div>
              <p className="text-white text-xs font-semibold">James Anderson</p>
              <p className="text-slate-500 text-xs">CFP · Senior Adviser</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800/60 px-7 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Client Dashboard</h1>
            <p className="text-slate-500 text-xs mt-0.5">Anderson Wealth Management</p>
          </div>
          <button
            onClick={onNewClient}
            className="flex items-center gap-2 px-5 py-2.5 bg-amber-400 text-slate-950 rounded-lg text-sm font-bold hover:bg-amber-300 transition-all shadow-lg shadow-amber-400/20"
          >
            <span className="text-base leading-none">+</span> New Client
          </button>
        </div>

        <div className="p-7 space-y-7">

          {/* Stats bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard icon="👥" label="Total Clients"   value={totalClients}  sub={`${activeClients} active`} />
            <StatCard icon="📄" label="Reports Generated" value={totalReports} sub="AI suitability reports" />
            <StatCard icon="💷" label="Clients Onboarded" value={activeClients} sub="Ready for analysis" />
          </div>

          {/* Main grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

            {/* Client list — spans 2 cols */}
            <div className="xl:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <h2 className="text-white font-semibold">All Clients</h2>
                <span className="text-xs text-slate-500">{totalClients} total</span>
              </div>

              {loading ? <Spinner /> : clients.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-6">
                  <div className="text-5xl mb-4">👥</div>
                  <p className="text-white font-semibold mb-2">No clients yet</p>
                  <p className="text-slate-400 text-sm mb-6">Add your first client to get started with AdviserOS</p>
                  <button onClick={onNewClient} className="px-6 py-2.5 bg-amber-400 text-slate-950 rounded-lg text-sm font-bold hover:bg-amber-300 transition-all">
                    + Add First Client
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-slate-800">
                  {clients.map((client) => (
                    <div key={client.id} className="px-6 py-4 hover:bg-slate-800/40 transition-colors">
                      <div className="flex items-start justify-between gap-4">
                        {/* Client info */}
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-300 text-sm font-bold shrink-0">
                            {client.first_name[0]}{client.last_name[0]}
                          </div>
                          <div className="min-w-0">
                            <p className="text-white font-semibold text-sm truncate">
                              {client.first_name} {client.last_name}
                            </p>
                            <p className="text-slate-400 text-xs truncate">{client.email}</p>
                            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                              <span className={`px-2 py-0.5 rounded-md text-xs border ${riskColour(client.risk_profile)}`}>
                                {client.risk_profile}
                              </span>
                              {client.annual_income && (
                                <span className="text-slate-500 text-xs">
                                  £{Number(client.annual_income).toLocaleString("en-GB")}/yr
                                </span>
                              )}
                              {!client.is_active && (
                                <span className="px-2 py-0.5 rounded-md text-xs bg-slate-800 text-slate-500 border border-slate-700">Inactive</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-1.5 flex-wrap shrink-0">
                          <ActionBtn colour="amber" onClick={() => setModal({ type: "profile", client })}>
                            View Profile
                          </ActionBtn>
                          <ActionBtn
                            colour="blue"
                            loading={actionLoad[`${client.id}_analyse`]}
                            onClick={() => runAnalysis(client)}
                          >
                            Run Analysis
                          </ActionBtn>
                          <ActionBtn
                            colour="emerald"
                            loading={actionLoad[`${client.id}_pdf`]}
                            onClick={() => downloadPDF(client)}
                          >
                            Download PDF
                          </ActionBtn>
                          <ActionBtn
                            colour="violet"
                            loading={actionLoad[`${client.id}_email`]}
                            onClick={() => viewEmail(client)}
                          >
                            View Email
                          </ActionBtn>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Activity feed */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-800">
                <h2 className="text-white font-semibold">Recent Activity</h2>
              </div>
              {loading ? <Spinner /> : activity.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center px-4">
                  <p className="text-slate-500 text-sm">No activity yet</p>
                  <p className="text-slate-600 text-xs mt-1">Run an analysis to see activity here</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-800/60">
                  {activity.map((r) => (
                    <div key={r.id} className="px-5 py-3.5 hover:bg-slate-800/30 transition-colors">
                      <div className="flex items-start gap-3">
                        <span className="text-lg shrink-0 mt-0.5">{activityIcon(r.title)}</span>
                        <div className="min-w-0">
                          <p className="text-white text-xs font-semibold truncate">{r.title}</p>
                          <p className="text-slate-500 text-xs mt-0.5">{timeAgo(r.created_at)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>
      </main>

      {/* Modals */}
      {modal?.type === "profile" && (
        <Modal title={`${modal.client.first_name} ${modal.client.last_name} — Profile`} onClose={() => setModal(null)}>
          <ProfileContent client={modal.client} />
        </Modal>
      )}
      {modal?.type === "email" && (
        <Modal title={`Email Draft — ${modal.client.first_name} ${modal.client.last_name}`} onClose={() => setModal(null)}>
          <EmailContent email={modal.data} />
        </Modal>
      )}

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-sm font-semibold shadow-xl border transition-all ${
          toast.ok
            ? "bg-emerald-900/90 border-emerald-700 text-emerald-300"
            : "bg-red-900/90 border-red-700 text-red-300"
        }`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}
