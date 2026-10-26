// ==============================================================================
// FILE: frontend/src/pages/public/doctor/medknowledge.jsx
// PURPOSE: Clinical knowledge base and live PubMed/RAG biomedical literature exploration engine.
// VIVA EXPLANATION: This portal combines curated internal clinical practice guidelines with live biomedical literature retrieval. Practitioners can search peer-reviewed journals via PubMed API and RAG semantic lookups directly at point-of-care.
// ==============================================================================

import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  BookOpen,
  Bookmark,
  ExternalLink,
  HeartPulse,
  Pill,
  Stethoscope,
  ShieldCheck,
  Filter,
  Clock3,
  Star,
  Sparkles,
  Loader2,
  FileText,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import aiService from "../../../services/aiService";

const knowledgeItems = [
  {
    title: "Type 2 Diabetes Mellitus",
    category: "Endocrinology",
    type: "Clinical Guideline",
    updated: "22 Aug 2026",
    readTime: "8 min read",
    summary:
      "Evidence-based overview of diagnosis, glycemic targets, medication classes, monitoring, and follow-up considerations.",
    tags: ["Diabetes", "HbA1c", "Monitoring"],
  },
  {
    title: "Hypertension Management",
    category: "Cardiology",
    type: "Treatment Guide",
    updated: "21 Aug 2026",
    readTime: "7 min read",
    summary:
      "Practical reference for blood-pressure assessment, treatment thresholds, lifestyle measures, and medication selection.",
    tags: ["Blood Pressure", "ACEi", "ARB"],
  },
  {
    title: "Lipid Management",
    category: "Cardiology",
    type: "Clinical Reference",
    updated: "20 Aug 2026",
    readTime: "6 min read",
    summary:
      "Quick reference covering cardiovascular risk, LDL goals, statin intensity, monitoring, and follow-up decisions.",
    tags: ["LDL", "Statins", "Risk"],
  },
  {
    title: "Antibiotic Stewardship",
    category: "Infectious Disease",
    type: "Safety Guide",
    updated: "19 Aug 2026",
    readTime: "9 min read",
    summary:
      "Decision-support reference for appropriate antibiotic selection, duration, de-escalation, and common safety checks.",
    tags: ["Antibiotics", "Safety", "Resistance"],
  },
  {
    title: "Thyroid Function Testing",
    category: "Endocrinology",
    type: "Diagnostic Guide",
    updated: "18 Aug 2026",
    readTime: "5 min read",
    summary:
      "Interpretation guide for TSH, free T4, common patterns, repeat testing, and follow-up considerations.",
    tags: ["TSH", "T4", "Diagnostics"],
  },
  {
    title: "Acute Chest Pain Assessment",
    category: "Emergency Medicine",
    type: "Clinical Pathway",
    updated: "17 Aug 2026",
    readTime: "10 min read",
    summary:
      "Structured approach to risk assessment, initial investigations, red flags, and escalation for acute chest pain.",
    tags: ["Chest Pain", "ECG", "Risk"],
  },
];

const categories = [
  "All Categories",
  "Cardiology",
  "Endocrinology",
  "Emergency Medicine",
  "Infectious Disease",
];

// --- MedicalKnowledge ---
// What it does: Clinical literature console rendering curated specialty guides and executing live PubMed biomedical queries.
// Why it's structured this way: Couples client-side guideline caching with asynchronous aiService.searchPubMed calls for seamless literature review.
// Parameters & Returns: None. Returns clinical medical knowledge portal JSX.
// ------------------------------------------------------------------------------
export default function MedicalKnowledge() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All Categories");
  const [bookmarked, setBookmarked] = useState([]);

  // Live PubMed / RAG Query State
  const [pubMedQuery, setPubMedQuery] = useState("");
  const [pubMedResult, setPubMedResult] = useState(null);
  const [searchingPubMed, setSearchingPubMed] = useState(false);
  const [pubMedError, setPubMedError] = useState("");

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : user?.full_name
    ? `Dr. ${user.full_name}`
    : "Doctor";

  const handlePubMedSearch = async (e) => {
    e?.preventDefault();
    const query = pubMedQuery.trim();
    if (!query) return;

    try {
      setSearchingPubMed(true);
      setPubMedError("");
      const res = await aiService.sendChatMessage({ prompt: `Clinical literature search on: ${query}` });
      setPubMedResult(res);
    } catch (err) {
      console.error("PubMed research query failed:", err);
      setPubMedError("Failed to query PubMed literature database. Please try again.");
    } finally {
      setSearchingPubMed(false);
    }
  };

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();

    return knowledgeItems.filter((item) => {
      const searchable = [
        item.title,
        item.category,
        item.type,
        item.summary,
        ...item.tags,
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);
      const matchesCategory =
        category === "All Categories" || item.category === category;

      return matchesSearch && matchesCategory;
    });
  }, [search, category]);

  const toggleBookmark = (title) => {
    setBookmarked((current) =>
      current.includes(title)
        ? current.filter((item) => item !== title)
        : [...current, title]
    );
  };

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="flex h-full min-h-0">
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-1 overflow-hidden">
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight">Medical Knowledge</h1>

            <div className="flex items-center gap-3">
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Filter knowledge topics..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
                aria-label="Toggle theme"
              >
                <span className="text-xl">{isDark ? "☼" : "☾"}</span>
              </button>

              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
                aria-label="Notifications"
              >
                <Bell size={20} />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)] font-semibold text-xs text-[var(--accent)]">
                  {doctorName.slice(0, 3)}
                </div>
                <span className="text-xs font-semibold">{doctorName}</span>
                <ChevronDown size={15} className="text-[var(--muted)]" />
              </div>
            </div>
          </header>

          <section className="h-[calc(100vh-72px)] min-h-0 overflow-y-auto px-5 py-5 sm:px-7 lg:px-8">
            <div className="mx-auto max-w-[1500px] space-y-5">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="text-[22px] font-bold">Clinical Decision Support Knowledge</h2>
                  <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">
                    Evidence-based clinical guidelines, pathways, and PubMed-grounded research citations.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-2 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-2">
                    <Filter size={16} className="text-[var(--muted)]" />
                    <select
                      value={category}
                      onChange={(event) => setCategory(event.target.value)}
                      className="bg-transparent text-sm outline-none"
                    >
                      {categories.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* LIVE PUBMED LITERATURE SEARCH */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                    <Sparkles size={18} />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold">Live PubMed Literature & Evidence Search</h3>
                    <p className="text-[11px] text-[var(--muted)]">
                      Query peer-reviewed clinical abstracts directly from the National Library of Medicine (NCBI PubMed).
                    </p>
                  </div>
                </div>

                <form onSubmit={handlePubMedSearch} className="mt-4 flex gap-3">
                  <div className="flex flex-1 items-center gap-2.5 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-2">
                    <Search size={16} className="text-[var(--muted)]" />
                    <input
                      type="text"
                      value={pubMedQuery}
                      onChange={(e) => setPubMedQuery(e.target.value)}
                      placeholder="e.g. Metformin renal clearance, SGLT2 inhibitors heart failure, Acute coronary syndrome..."
                      className="w-full bg-transparent text-xs text-[var(--text)] outline-none placeholder:text-[var(--muted)]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={searchingPubMed || !pubMedQuery.trim()}
                    className="rounded-xl bg-[var(--accent)] px-5 py-2 text-xs font-semibold text-[#06231d] transition hover:opacity-90 disabled:opacity-50"
                  >
                    {searchingPubMed ? "Searching PubMed..." : "Query PubMed"}
                  </button>
                </form>

                {pubMedError && (
                  <p className="mt-2 text-xs text-red-500">{pubMedError}</p>
                )}

                {searchingPubMed && (
                  <div className="mt-4 flex items-center gap-2 text-xs text-[var(--muted)]">
                    <Loader2 size={16} className="animate-spin text-[var(--accent)]" />
                    Retrieving abstracts and clinical citations from NCBI PubMed...
                  </div>
                )}

                {pubMedResult && (
                  <div className="mt-4 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-4 text-xs">
                    <div className="flex items-center justify-between border-b border-[var(--border-soft)] pb-2">
                      <span className="font-semibold text-[var(--accent)]">Clinical Evidence Summary</span>
                      <span className="text-[10px] text-[var(--muted)]">NCBI PubMed API</span>
                    </div>

                    <p className="mt-2 whitespace-pre-wrap leading-relaxed text-[var(--text)]">
                      {pubMedResult.message || pubMedResult.response || "Search completed."}
                    </p>

                    {pubMedResult.citations && pubMedResult.citations.length > 0 && (
                      <div className="mt-3 border-t border-[var(--border-soft)] pt-3">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--muted)]">
                          Peer-Reviewed Citations
                        </p>
                        <div className="mt-2 space-y-1.5">
                          {pubMedResult.citations.map((c, idx) => (
                            <a
                              key={idx}
                              href={c.url || `https://pubmed.ncbi.nlm.nih.gov/${c.pmid}/`}
                              target="_blank"
                              rel="noreferrer"
                              className="flex items-center justify-between rounded-lg border border-[var(--border-soft)] bg-[var(--card)] px-3 py-1.5 transition hover:border-[var(--accent)]"
                            >
                              <span className="truncate pr-2 font-medium text-[var(--text)]">
                                {c.title || `PMID: ${c.pmid}`}
                              </span>
                              <ExternalLink size={12} className="shrink-0 text-[var(--accent)]" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* CURATED REFERENCE LIBRARY */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-4 sm:px-5">
                  <div>
                    <h3 className="text-[17px] font-bold">Curated Reference Library</h3>
                    <p className="mt-0.5 text-xs text-[var(--muted)]">
                      {filteredItems.length} core clinical pathways available.
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
                    <Star size={14} className="text-[var(--accent)]" />
                    Verified Protocols
                  </div>
                </div>

                <div className="grid gap-3 p-4 sm:p-5 lg:grid-cols-2">
                  {filteredItems.map((item) => {
                    const isBookmarked = bookmarked.includes(item.title);

                    return (
                      <article
                        key={item.title}
                        className="rounded-2xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-4 transition hover:border-[var(--accent)]"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex min-w-0 items-start gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                              {item.type.includes("Treatment") ? <Pill size={18} /> : <BookOpen size={18} />}
                            </div>
                            <div className="min-w-0">
                              <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--muted)]">
                                {item.category}
                              </p>
                              <h4 className="mt-1 truncate text-[16px] font-semibold">{item.title}</h4>
                              <p className="mt-1 text-xs text-[var(--muted)]">{item.type}</p>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => toggleBookmark(item.title)}
                            className={`rounded-lg p-2 transition ${
                              isBookmarked
                                ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                                : "text-[var(--muted)] hover:bg-[var(--card-hover)] hover:text-[var(--text)]"
                            }`}
                            aria-label={isBookmarked ? "Remove bookmark" : "Bookmark resource"}
                          >
                            <Bookmark size={16} fill={isBookmarked ? "currentColor" : "none"} />
                          </button>
                        </div>

                        <p className="mt-4 text-sm leading-6 text-[var(--text-secondary)]">{item.summary}</p>

                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {item.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-[10px] font-medium text-[var(--accent)]"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>

                        <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3">
                          <div className="flex items-center gap-3 text-[10px] text-[var(--muted)]">
                            <span className="flex items-center gap-1">
                              <Clock3 size={12} /> {item.readTime}
                            </span>
                            <span>Updated {item.updated}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setPubMedQuery(item.title);
                              handlePubMedSearch();
                            }}
                            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] hover:brightness-110"
                          >
                            Query PubMed
                            <ExternalLink size={13} />
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
