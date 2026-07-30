import { useState } from "react";

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (val) => {
  const raw = String(val).replace(/[^0-9]/g, "");
  if (!raw) return "";
  return Number(raw).toLocaleString("en-GB");
};
const unformat = (val) => String(val).replace(/,/g, "");

function CurrencyInput({ label, name, value, onChange, placeholder = "0" }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-semibold text-sm">£</span>
        <input
          type="text"
          inputMode="numeric"
          value={fmt(value)}
          placeholder={placeholder}
          onChange={(e) => onChange(name, unformat(e.target.value))}
          className="w-full pl-7 pr-4 py-3 bg-slate-800/60 border border-slate-700 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/30 transition-all text-sm"
        />
      </div>
    </div>
  );
}

function TextInput({ label, name, value, onChange, placeholder = "", type = "text" }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)}
        className="w-full px-4 py-3 bg-slate-800/60 border border-slate-700 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/30 transition-all text-sm"
      />
    </div>
  );
}

function SelectInput({ label, name, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        className="w-full px-4 py-3 bg-slate-800/60 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/30 transition-all text-sm appearance-none cursor-pointer"
      >
        <option value="" disabled>Select…</option>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function TextArea({ label, name, value, onChange, placeholder = "" }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</label>
      <textarea
        rows={3}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)}
        className="w-full px-4 py-3 bg-slate-800/60 border border-slate-700 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/30 transition-all text-sm resize-none"
      />
    </div>
  );
}

// ── Step definitions ──────────────────────────────────────────────────────────
const STEPS = [
  { id: 1, title: "Personal Details",      icon: "👤" },
  { id: 2, title: "Income & Expenditure",  icon: "💷" },
  { id: 3, title: "Assets & Liabilities",  icon: "🏠" },
  { id: 4, title: "Previous Investments",  icon: "📈" },
  { id: 5, title: "Goals & Risk",          icon: "🎯" },
];

const INITIAL = {
  // Step 1
  first_name: "", last_name: "", age: "", employment_status: "",
  marital_status: "", dependants: "", uk_domicile: "",
  // Step 2
  annual_salary: "", dividend_income: "", rental_income: "",
  monthly_expenses: "", monthly_debt_repayments: "",
  // Step 3
  property_value: "", mortgage_outstanding: "", total_savings: "",
  isa_balance: "", pension_value: "", other_loans: "",
  // Step 4
  investments: [{ fund_name: "", amount_invested: "", date_recommended: "", current_value: "" }],
  // Step 5
  short_term_goal: "", medium_term_goal: "", long_term_goal: "",
  target_retirement_age: "", risk_tolerance: "",
};

// ── Steps ─────────────────────────────────────────────────────────────────────
function Step1({ data, set }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <TextInput label="First Name"   name="first_name" value={data.first_name} onChange={set} placeholder="Eleanor" />
      <TextInput label="Last Name"    name="last_name"  value={data.last_name}  onChange={set} placeholder="Hartwell" />
      <TextInput label="Age"          name="age"        value={data.age}        onChange={set} placeholder="42" type="number" />
      <SelectInput label="Employment Status" name="employment_status" value={data.employment_status} onChange={set}
        options={[
          { value: "employed",      label: "Employed" },
          { value: "self_employed", label: "Self-Employed" },
          { value: "director",      label: "Company Director" },
          { value: "retired",       label: "Retired" },
        ]}
      />
      <SelectInput label="Marital Status" name="marital_status" value={data.marital_status} onChange={set}
        options={[
          { value: "single",    label: "Single" },
          { value: "married",   label: "Married" },
          { value: "divorced",  label: "Divorced" },
          { value: "widowed",   label: "Widowed" },
        ]}
      />
      <TextInput label="Number of Dependants" name="dependants" value={data.dependants} onChange={set} placeholder="0" type="number" />
      <SelectInput label="UK Domicile" name="uk_domicile" value={data.uk_domicile} onChange={set}
        options={[
          { value: "yes", label: "Yes" },
          { value: "no",  label: "No"  },
        ]}
      />
    </div>
  );
}

function Step2({ data, set }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <CurrencyInput label="Annual Salary"           name="annual_salary"           value={data.annual_salary}           onChange={set} />
      <CurrencyInput label="Dividend Income (p.a.)"  name="dividend_income"          value={data.dividend_income}          onChange={set} />
      <CurrencyInput label="Rental Income (p.a.)"    name="rental_income"            value={data.rental_income}            onChange={set} />
      <CurrencyInput label="Monthly Expenses"        name="monthly_expenses"         value={data.monthly_expenses}         onChange={set} />
      <CurrencyInput label="Monthly Debt Repayments" name="monthly_debt_repayments"  value={data.monthly_debt_repayments}  onChange={set} />
    </div>
  );
}

function Step3({ data, set }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <CurrencyInput label="Property Value"        name="property_value"        value={data.property_value}        onChange={set} />
      <CurrencyInput label="Mortgage Outstanding"  name="mortgage_outstanding"  value={data.mortgage_outstanding}  onChange={set} />
      <CurrencyInput label="Total Savings"         name="total_savings"         value={data.total_savings}         onChange={set} />
      <CurrencyInput label="ISA Balance"           name="isa_balance"           value={data.isa_balance}           onChange={set} />
      <CurrencyInput label="Pension Value"         name="pension_value"         value={data.pension_value}         onChange={set} />
      <CurrencyInput label="Other Loans"           name="other_loans"           value={data.other_loans}           onChange={set} />
    </div>
  );
}

function Step4({ data, set }) {
  const updateRow = (i, field, val) => {
    const rows = [...data.investments];
    rows[i] = { ...rows[i], [field]: val };
    set("investments", rows);
  };
  const addRow = () => set("investments", [...data.investments, { fund_name: "", amount_invested: "", date_recommended: "", current_value: "" }]);
  const removeRow = (i) => set("investments", data.investments.filter((_, idx) => idx !== i));

  return (
    <div className="flex flex-col gap-4">
      {data.investments.map((row, i) => (
        <div key={i} className="relative bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="absolute top-3 right-3">
            {data.investments.length > 1 && (
              <button onClick={() => removeRow(i)} className="text-slate-500 hover:text-red-400 text-lg leading-none transition-colors">×</button>
            )}
          </div>
          <TextInput    label="Fund Name"          name="fund_name"         value={row.fund_name}         onChange={(_, v) => updateRow(i, "fund_name", v)}         placeholder="e.g. Vanguard LifeStrategy" />
          <CurrencyInput label="Amount Invested"   name="amount_invested"   value={row.amount_invested}   onChange={(_, v) => updateRow(i, "amount_invested", v)} />
          <TextInput    label="Date Recommended"   name="date_recommended"  value={row.date_recommended}  onChange={(_, v) => updateRow(i, "date_recommended", v)}  type="date" />
          <CurrencyInput label="Current Value"     name="current_value"     value={row.current_value}     onChange={(_, v) => updateRow(i, "current_value", v)} />
        </div>
      ))}
      <button
        onClick={addRow}
        className="flex items-center gap-2 text-amber-400 hover:text-amber-300 text-sm font-semibold transition-colors self-start mt-1"
      >
        <span className="text-lg leading-none">+</span> Add Another Investment
      </button>
    </div>
  );
}

function Step5({ data, set }) {
  return (
    <div className="grid grid-cols-1 gap-5">
      <TextArea label="Short Term Goal (0–2 years)"   name="short_term_goal"   value={data.short_term_goal}   onChange={set} placeholder="e.g. Build 6-month emergency fund, clear credit card debt" />
      <TextArea label="Medium Term Goal (2–10 years)" name="medium_term_goal"  value={data.medium_term_goal}  onChange={set} placeholder="e.g. Save for children's education, purchase buy-to-let" />
      <TextArea label="Long Term Goal (10+ years)"    name="long_term_goal"    value={data.long_term_goal}    onChange={set} placeholder="e.g. Retire comfortably, leave inheritance for children" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <TextInput label="Target Retirement Age" name="target_retirement_age" value={data.target_retirement_age} onChange={set} placeholder="65" type="number" />
        <SelectInput label="Risk Tolerance" name="risk_tolerance" value={data.risk_tolerance} onChange={set}
          options={[
            { value: "low",    label: "Low — Capital preservation priority" },
            { value: "medium", label: "Medium — Balanced growth & security" },
            { value: "high",   label: "High — Maximum growth potential" },
          ]}
        />
      </div>
    </div>
  );
}

// ── Success Screen ─────────────────────────────────────────────────────────────
function SuccessScreen({ name, onBack }) {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-full bg-emerald-500/20 border-2 border-emerald-400 flex items-center justify-center mx-auto mb-6 text-4xl">
          ✓
        </div>
        <h2 className="text-3xl font-bold text-white mb-3" style={{ fontFamily: "'Georgia', serif" }}>
          Profile Created
        </h2>
        <p className="text-slate-400 text-lg mb-2">
          <span className="text-white font-semibold">{name}</span> has been successfully added to AdviserOS.
        </p>
        <p className="text-slate-500 text-sm">The client profile is now available in your dashboard.</p>
        <div className="mt-8 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
        <p className="mt-6 text-emerald-400 text-xs font-semibold uppercase tracking-widest">AdviserOS · Client Onboarding</p>
<button onClick={onBack} className="mt-6 px-6 py-2.5 bg-emerald-500 text-white rounded-lg text-sm font-semibold hover:bg-emerald-400 transition-all">
  Back to Dashboard →
</button>
      </div>
    </div>
  );
}

// ── Main Wizard ───────────────────────────────────────────────────────────────
export default function ClientProfileWizard({ onSuccess }) {
  const [step, setStep]       = useState(1);
  const [data, setData]       = useState(INITIAL);
  const [submitted, setSubmit] = useState(false);
  const [loading, setLoading]  = useState(false);
  const [error, setError]      = useState("");

  const set = (name, value) => setData((d) => ({ ...d, [name]: value }));

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = {
        first_name: data.first_name,
        last_name:  data.last_name,
        email:      `${data.first_name.toLowerCase()}.${data.last_name.toLowerCase()}@adviseros.com`,
        risk_profile: data.risk_tolerance === "low" ? "conservative" : data.risk_tolerance === "high" ? "aggressive" : "moderate",
        net_worth: Number(unformat(data.total_savings) || 0) + Number(unformat(data.pension_value) || 0) + Number(unformat(data.isa_balance) || 0),
        annual_income: Number(unformat(data.annual_salary) || 0),
        notes: `Goals: ${data.short_term_goal} | ${data.medium_term_goal} | ${data.long_term_goal}`,
      };
      const res = await fetch("http://localhost:8000/api/v1/clients/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Submission failed");
      }
      setSubmit(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) return <SuccessScreen name={`${data.first_name} ${data.last_name}`} onBack={onSuccess} />;

  const progress = ((step - 1) / (STEPS.length - 1)) * 100;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col" style={{ fontFamily: "'Georgia', serif" }}>
      {/* Top bar */}
      <div className="border-b border-slate-800/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-400 flex items-center justify-center">
            <span className="text-slate-950 font-bold text-sm">A</span>
          </div>
          <span className="text-white font-semibold tracking-wide text-sm">AdviserOS</span>
        </div>
        <span className="text-slate-500 text-xs uppercase tracking-widest">Client Onboarding</span>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="hidden md:flex flex-col w-64 border-r border-slate-800/60 p-6 gap-2 shrink-0">
          <p className="text-slate-500 text-xs uppercase tracking-widest mb-4">Sections</p>
          {STEPS.map((s) => (
            <div
              key={s.id}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                s.id === step
                  ? "bg-amber-400/10 border border-amber-400/30"
                  : s.id < step
                  ? "opacity-60"
                  : "opacity-30"
              }`}
            >
              <span className="text-base">{s.icon}</span>
              <span className={`text-sm ${s.id === step ? "text-amber-300 font-semibold" : "text-slate-400"}`}>
                {s.title}
              </span>
              {s.id < step && <span className="ml-auto text-emerald-400 text-xs">✓</span>}
            </div>
          ))}
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          {/* Progress bar */}
          <div className="px-8 pt-8 pb-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-500 uppercase tracking-widest">
                Step {step} of {STEPS.length}
              </span>
              <span className="text-xs text-amber-400 font-semibold">{Math.round(progress)}% complete</span>
            </div>
            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-amber-500 to-amber-300 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Form card */}
          <div className="flex-1 p-8">
            <div className="max-w-2xl mx-auto">
              {/* Section header */}
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{STEPS[step - 1].icon}</span>
                  <h1 className="text-2xl font-bold text-white">{STEPS[step - 1].title}</h1>
                </div>
                <div className="h-px bg-gradient-to-r from-amber-400/40 to-transparent" />
              </div>

              {/* Step content */}
              <div className="animate-fade">
                {step === 1 && <Step1 data={data} set={set} />}
                {step === 2 && <Step2 data={data} set={set} />}
                {step === 3 && <Step3 data={data} set={set} />}
                {step === 4 && <Step4 data={data} set={set} />}
                {step === 5 && <Step5 data={data} set={set} />}
              </div>

              {/* Error */}
              {error && (
                <div className="mt-6 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  ⚠️ {error}
                </div>
              )}

              {/* Navigation */}
              <div className="flex items-center justify-between mt-10 pt-6 border-t border-slate-800">
                <button
                  onClick={() => setStep((s) => s - 1)}
                  disabled={step === 1}
                  className="px-6 py-2.5 text-sm text-slate-400 border border-slate-700 rounded-lg hover:border-slate-500 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-all"
                >
                  ← Back
                </button>

                {step < STEPS.length ? (
                  <button
                    onClick={() => setStep((s) => s + 1)}
                    className="px-8 py-2.5 text-sm font-semibold bg-amber-400 text-slate-950 rounded-lg hover:bg-amber-300 transition-all shadow-lg shadow-amber-400/20"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="px-8 py-2.5 text-sm font-semibold bg-emerald-500 text-white rounded-lg hover:bg-emerald-400 disabled:opacity-60 transition-all shadow-lg shadow-emerald-500/20"
                  >
                    {loading ? "Submitting…" : "Submit Profile ✓"}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
