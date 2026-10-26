// ==============================================================================
// FILE: frontend/src/pages/public/patient/patient_shared.jsx
// PURPOSE: Reusable atomic UI components and style helpers for patient portal interfaces.
// VIVA EXPLANATION: Implements the shared component library for patient interfaces. Encapsulates design tokens (surface, inputStyle, status badges), accessible modals, metric stat cards, and section card containers to ensure consistent clinical UX across all patient pages.
// ==============================================================================

import React, { useEffect } from "react";
import {
  AlertCircle,
  Check,
  ChevronDown,
  Download,
  FileText,
  Info,
  Loader2,
  Search,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";

export const cx = (...parts) => parts.filter(Boolean).join(" ");

export const surface = (darkMode = false) =>
  darkMode
    ? "border-slate-800 bg-[#15211f] text-slate-100"
    : "border-slate-200 bg-white text-slate-900";

export const pageText = (darkMode = false) =>
  darkMode ? "text-white" : "text-emerald-950";

export const mutedText = (darkMode = false) =>
  darkMode ? "text-slate-400" : "text-slate-500";

export const inputStyle = (darkMode = false) =>
  darkMode
    ? "border-slate-700 bg-[#101918] text-slate-100 placeholder:text-slate-500 focus:border-emerald-400"
    : "border-slate-200 bg-white text-slate-800 placeholder:text-slate-400 focus:border-emerald-500";


// --- PageHeader ---
// What it does: Standardized top header with title, eyebrow category, and action button slots.
// Why it's structured this way: Enforces uniform typographic hierarchy across all patient views.
// Parameters & Returns: { darkMode, eyebrow, title, description, action } -> Header JSX element.
// ------------------------------------------------------------------------------
export function PageHeader({ darkMode, eyebrow, title, description, action }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        {eyebrow && (
          <p className={cx("mb-1 text-xs font-semibold uppercase tracking-[0.12em]", mutedText(darkMode))}>
            {eyebrow}
          </p>
        )}
        <h1 className={cx("text-[28px] font-bold tracking-[-0.8px]", pageText(darkMode))}>{title}</h1>
        {description && <p className={cx("mt-1 max-w-2xl text-sm", mutedText(darkMode))}>{description}</p>}
      </div>
      {action}
    </div>
  );
}


// --- SectionCard ---
// What it does: Container card component wrapping functional patient widgets with borders and padding.
// Why it's structured this way: Promotes consistent card surfaces and dark-theme compliance.
// Parameters & Returns: { darkMode, title, description, action, children, className } -> Section card JSX.
// ------------------------------------------------------------------------------
export function SectionCard({ darkMode, title, description, action, children, className = "" }) {

  return (
    <section className={cx("rounded-[18px] border p-5 shadow-[0_3px_15px_rgba(15,23,42,0.025)]", surface(darkMode), className)}>
      {(title || description || action) && (
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title && <h2 className={cx("text-[17px] font-bold", pageText(darkMode))}>{title}</h2>}
            {description && <p className={cx("mt-1 text-sm", mutedText(darkMode))}>{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function PrimaryButton({ darkMode, children, icon: Icon, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-emerald-500 text-white hover:bg-emerald-600",
    secondary: darkMode
      ? "border border-slate-700 bg-slate-900/40 text-slate-200 hover:bg-slate-800"
      : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
    quiet: darkMode ? "text-emerald-300 hover:bg-emerald-500/10" : "text-emerald-700 hover:bg-emerald-50",
    danger: darkMode ? "border border-rose-900/60 bg-rose-950/20 text-rose-300 hover:bg-rose-950/40" : "border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100",
  };
  return (
    <button className={cx("inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-emerald-400/50", styles[variant], className)} {...props}>
      {Icon && <Icon size={16} strokeWidth={1.9} />}
      {children}
    </button>
  );
}

export function IconButton({ darkMode, label, children, className = "", ...props }) {
  return (
    <button aria-label={label} title={label} className={cx("inline-flex h-9 w-9 items-center justify-center rounded-lg transition focus:outline-none focus:ring-2 focus:ring-emerald-400/50", darkMode ? "text-slate-300 hover:bg-slate-800" : "text-slate-500 hover:bg-slate-50", className)} {...props}>
      {children}
    </button>
  );
}

export function StatCard({ darkMode, label, value, detail, icon: Icon, tone = "green" }) {
  const iconTone = tone === "soft" ? (darkMode ? "bg-slate-800 text-slate-300" : "bg-slate-100 text-slate-600") : darkMode ? "bg-emerald-500/10 text-emerald-300" : "bg-emerald-50 text-emerald-600";
  return (
    <div className={cx("rounded-[18px] border p-5 shadow-[0_3px_15px_rgba(15,23,42,0.025)]", surface(darkMode))}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={cx("text-sm font-medium", mutedText(darkMode))}>{label}</p>
          <p className={cx("mt-2 text-[28px] font-bold tracking-[-0.7px]", pageText(darkMode))}>{value}</p>
          {detail && <p className={cx("mt-1 text-xs", mutedText(darkMode))}>{detail}</p>}
        </div>
        {Icon && <div className={cx("flex h-11 w-11 shrink-0 items-center justify-center rounded-full", iconTone)}><Icon size={21} strokeWidth={1.8} /></div>}
      </div>
    </div>
  );
}

const statusStyles = {
  Normal: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  Completed: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  Active: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  Pending: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  Abnormal: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  Cancelled: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
  Scheduled: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  "Not taken": "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
};

export function StatusBadge({ darkMode, status }) {
  const light = {
    Normal: "bg-emerald-50 text-emerald-700",
    Completed: "bg-emerald-50 text-emerald-700",
    Active: "bg-emerald-50 text-emerald-700",
    Pending: "bg-slate-100 text-slate-600",
    Abnormal: "bg-amber-50 text-amber-700",
    Cancelled: "bg-rose-50 text-rose-700",
    Scheduled: "bg-emerald-50 text-emerald-700",
    "Not taken": "bg-amber-50 text-amber-700",
  };
  const dark = {
    Normal: "bg-emerald-500/10 text-emerald-300",
    Completed: "bg-emerald-500/10 text-emerald-300",
    Active: "bg-emerald-500/10 text-emerald-300",
    Pending: "bg-slate-800 text-slate-300",
    Abnormal: "bg-amber-500/10 text-amber-300",
    Cancelled: "bg-rose-500/10 text-rose-300",
    Scheduled: "bg-emerald-500/10 text-emerald-300",
    "Not taken": "bg-amber-500/10 text-amber-300",
  };
  const classes = (darkMode ? dark : light)[status] || (darkMode ? "bg-slate-800 text-slate-300" : "bg-slate-100 text-slate-600");
  return <span className={cx("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", classes)}>{status}</span>;
}

export function SearchField({ darkMode, value, onChange, placeholder = "Search..." }) {
  return (
    <label className={cx("flex h-10 min-w-[220px] flex-1 items-center gap-2 rounded-xl border px-3", inputStyle(darkMode))}>
      <Search size={17} className="shrink-0 text-slate-500" />
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="w-full bg-transparent text-sm outline-none" />
    </label>
  );
}

export function SelectField({ darkMode, label, value, onChange, options }) {
  return (
    <label className="relative block">
      {label && <span className={cx("mb-1.5 block text-xs font-semibold", mutedText(darkMode))}>{label}</span>}
      <select value={value} onChange={(event) => onChange(event.target.value)} className={cx("h-10 appearance-none rounded-xl border px-3 pr-9 text-sm outline-none transition focus:ring-2 focus:ring-emerald-400/30", inputStyle(darkMode))}>
        {options.map((option) => <option key={option.value ?? option} value={option.value ?? option}>{option.label ?? option}</option>)}
      </select>
      <ChevronDown size={15} className="pointer-events-none absolute right-3 bottom-3 text-slate-500" />
    </label>
  );
}

export function Tabs({ darkMode, items, value, onChange }) {
  return (
    <div className={cx("inline-flex flex-wrap gap-1 rounded-xl p-1", darkMode ? "bg-slate-900/60" : "bg-slate-50")} role="tablist">
      {items.map((item) => (
        <button key={item.value} role="tab" aria-selected={value === item.value} onClick={() => onChange(item.value)} className={cx("rounded-lg px-3 py-2 text-xs font-semibold transition", value === item.value ? "bg-emerald-500 text-white shadow-sm" : mutedText(darkMode))}>{item.label}</button>
      ))}
    </div>
  );
}

export function ProgressBar({ darkMode, value, label, caption }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3 text-sm"><span className={cx("font-medium", pageText(darkMode))}>{label}</span><span className={cx("text-xs", mutedText(darkMode))}>{caption || `${value}%`}</span></div>
      <div className={cx("h-2 overflow-hidden rounded-full", darkMode ? "bg-slate-800" : "bg-slate-100")}><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>
    </div>
  );
}

export function SafetyNote({ darkMode, children = "This information is for decision support and should be reviewed with a healthcare professional." }) {
  return <div className={cx("flex gap-3 rounded-xl border px-4 py-3 text-xs leading-5", darkMode ? "border-emerald-900/70 bg-emerald-500/5 text-slate-300" : "border-emerald-100 bg-emerald-50/60 text-slate-600")}><ShieldCheck size={17} className="mt-0.5 shrink-0 text-emerald-500" /><p>{children}</p></div>;
}

export function EmptyState({ darkMode, title, description, action }) {
  return <div className={cx("rounded-xl border border-dashed px-6 py-10 text-center", darkMode ? "border-slate-700" : "border-slate-200")}><FileText size={25} className="mx-auto text-slate-400" /><h3 className={cx("mt-3 text-sm font-bold", pageText(darkMode))}>{title}</h3><p className={cx("mx-auto mt-1 max-w-md text-sm", mutedText(darkMode))}>{description}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

export function LoadingState({ darkMode, label = "Loading your information..." }) {
  return <div className={cx("flex items-center justify-center gap-2 rounded-xl border px-6 py-12 text-sm", darkMode ? "border-slate-800 text-slate-400" : "border-slate-200 text-slate-500")}><Loader2 size={18} className="animate-spin text-emerald-500" />{label}</div>;
}

export function Modal({ darkMode, open, title, onClose, children, footer }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => event.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && onClose?.()}><div className={cx("max-h-[90vh] w-full max-w-xl overflow-auto rounded-2xl border p-5 shadow-2xl", surface(darkMode))}><div className="flex items-center justify-between gap-3"><h2 className={cx("text-lg font-bold", pageText(darkMode))}>{title}</h2><IconButton darkMode={darkMode} label="Close" onClick={onClose}><X size={18} /></IconButton></div><div className="mt-5">{children}</div>{footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}</div></div>;
}

export function UploadButton({ darkMode, onSelect, children = "Upload" }) {
  return <label className={cx("inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition", darkMode ? "border-slate-700 text-slate-200 hover:bg-slate-800" : "border-slate-200 text-slate-700 hover:bg-slate-50")}><Upload size={16} /><span>{children}</span><input type="file" className="sr-only" accept=".pdf,.png,.jpg,.jpeg" onChange={(event) => onSelect?.(event.target.files?.[0])} /></label>;
}

export function Field({ darkMode, label, value, onChange, type = "text", placeholder }) {
  return <label className="block"><span className={cx("mb-1.5 block text-xs font-semibold", mutedText(darkMode))}>{label}</span><input type={type} value={value} onChange={onChange} placeholder={placeholder} className={cx("h-10 w-full rounded-xl border px-3 text-sm outline-none transition focus:ring-2 focus:ring-emerald-400/30", inputStyle(darkMode))} /></label>;
}

export function Notice({ darkMode, type = "info", children }) {
  const Icon = type === "error" ? AlertCircle : type === "success" ? Check : Info;
  const colors = type === "error" ? "border-rose-200 bg-rose-50 text-rose-700" : type === "success" ? "border-emerald-100 bg-emerald-50 text-emerald-700" : darkMode ? "border-slate-700 bg-slate-900/50 text-slate-300" : "border-slate-200 bg-slate-50 text-slate-600";
  return <div className={cx("flex items-start gap-2 rounded-xl border px-3 py-2.5 text-sm", colors)}><Icon size={16} className="mt-0.5 shrink-0" />{children}</div>;
}

export function DownloadAction({ darkMode, onClick }) { return <IconButton darkMode={darkMode} label="Download" onClick={onClick}><Download size={17} /></IconButton>; }

export function ChartTooltip({ darkMode, active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className={cx("rounded-xl border px-3 py-2 text-xs shadow-lg", surface(darkMode))}><p className="mb-1 font-semibold">{label}</p>{payload.map((item) => <p key={item.dataKey} className="flex items-center justify-between gap-4"><span className="text-slate-500">{item.name}</span><strong className="text-emerald-500">{item.value}</strong></p>)}</div>;
}
