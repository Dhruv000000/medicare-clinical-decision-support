import React from "react";
import { Bell, Check, Globe2, Monitor, Moon, Save, Sun, UserRound } from "lucide-react";
import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";

export default function Settings({ embedded = false }) {
  const { isDark, toggleTheme } = useTheme();
  const [saved, setSaved] = React.useState(false);
  const [notifications, setNotifications] = React.useState(true);
  const [emailAlerts, setEmailAlerts] = React.useState(true);
  const [compactMode, setCompactMode] = React.useState(false);

  const saveSettings = () => {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  };

  return (
    <div
      className="min-h-screen bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      {!embedded && <Sidebar />}

      <main className={embedded ? "min-h-screen w-full" : "ml-[255px] min-h-screen w-[calc(100%-255px)] min-w-0 flex-none"}>
        <header className="flex min-h-[72px] items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--bg)] px-5 sm:px-7 lg:px-8">
          <div>
            <h1 className="text-[26px] font-bold tracking-tight sm:text-[30px]">Settings</h1>
            <p className="mt-1 text-xs text-[var(--muted)]">Manage your doctor account and dashboard preferences.</p>
          </div>

          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)] transition hover:bg-[var(--card-hover)]"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>

        <section className="min-h-[calc(100vh-72px)] px-5 py-5 sm:px-7 lg:px-8">
          <div className="mx-auto grid max-w-6xl gap-4 lg:grid-cols-[1.15fr_.85fr]">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 sm:p-6">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]">
                  <UserRound size={19} />
                </div>
                <div>
                  <h2 className="text-[18px] font-bold">Profile</h2>
                  <p className="text-xs text-[var(--muted)]">Doctor account information</p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="text-sm">
                  <span className="mb-2 block text-[var(--muted)]">Full name</span>
                  <input defaultValue="Dr. Olivia" className="w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-3 outline-none transition focus:border-[var(--accent)]" />
                </label>
                <label className="text-sm">
                  <span className="mb-2 block text-[var(--muted)]">Role</span>
                  <input defaultValue="Physician" className="w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-3 outline-none transition focus:border-[var(--accent)]" />
                </label>
                <label className="text-sm sm:col-span-2">
                  <span className="mb-2 block text-[var(--muted)]">Email</span>
                  <input defaultValue="olivia@medicare.local" type="email" className="w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-3 outline-none transition focus:border-[var(--accent)]" />
                </label>
              </div>
            </div>

            <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 sm:p-6">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]">
                  <Bell size={19} />
                </div>
                <div>
                  <h2 className="text-[18px] font-bold">Preferences</h2>
                  <p className="text-xs text-[var(--muted)]">Control your dashboard experience</p>
                </div>
              </div>

              <div className="space-y-3">
                <SettingToggle label="Notifications" description="Show in-app patient and review alerts." enabled={notifications} onChange={setNotifications} />
                <SettingToggle label="Email alerts" description="Receive important clinical updates by email." enabled={emailAlerts} onChange={setEmailAlerts} />
                <SettingToggle label="Compact mode" description="Use tighter spacing across doctor pages." enabled={compactMode} onChange={setCompactMode} />
              </div>

              <div className="mt-5 border-t border-[var(--border)] pt-5">
                <p className="mb-2 text-xs font-medium text-[var(--muted)]">Theme</p>
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="flex w-full items-center justify-between rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-3 text-sm transition hover:bg-[var(--card-hover)]"
                >
                  <span className="flex items-center gap-3"><Monitor size={17} className="text-[var(--accent)]" /> Global {isDark ? "Dark" : "Light"} theme</span>
                  <span className="text-xs text-[var(--muted)]">Change</span>
                </button>
              </div>
            </div>
          </div>

          <div className="mt-4 mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <p className="text-sm text-[var(--muted)]">Your settings are local to this dashboard until backend persistence is connected.</p>
            <button type="button" onClick={saveSettings} className="flex shrink-0 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#06231d] transition hover:brightness-105">
              {saved ? <Check size={17} /> : <Save size={17} />}
              {saved ? "Saved" : "Save settings"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

function SettingToggle({ label, description, enabled, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className="flex w-full items-center justify-between gap-4 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-3 text-left transition hover:bg-[var(--card-hover)]"
    >
      <span className="min-w-0">
        <span className="block text-sm font-medium">{label}</span>
        <span className="mt-0.5 block text-xs text-[var(--muted)]">{description}</span>
      </span>
      <span className={`relative h-6 w-11 shrink-0 rounded-full transition ${enabled ? "bg-[var(--accent)]" : "bg-[var(--track)]"}`}>
        <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition ${enabled ? "left-6" : "left-1"}`} />
      </span>
    </button>
  );
}
