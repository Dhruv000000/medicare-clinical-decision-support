// ==============================================================================
// FILE: frontend/src/pages/public/Landing.jsx
// PURPOSE: Public product homepage presenting clinical decision support features, explanations, and navigation.
// VIVA EXPLANATION: Serves as the public-facing promotional and overview portal for MediCare CDSS. Details core capabilities (AI symptom analysis, disease risk scoring with SHAP explanations, lab report parsing, OpenFDA safety), FAQs, and links to registration and sign-in.
// ==============================================================================

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../context/ThemeContext";
import {
  ArrowUpRight,
  ArrowRight,
  Check,
  ChevronDown,
  HeartPulse,
  ShieldCheck,
  Stethoscope,
  FileText,
  Users,
  Activity,
  Star,
  Menu,
  X,
  Plus,
} from "lucide-react";
import { Moon, Sun } from "lucide-react";
import ThemeToggle from "../../components/ThemeToggle";

const COLOR_SYSTEM = {
  primary: "#0FA37F",
  darkGreen: "#087F68",
  forest: "#123D32",
  lightMint: "#E8F7F2",
  veryLightMint: "#F4FBF8",
  warmWhite: "#FFFEFC",
  white: "#FFFFFF",
  text: "#5F6B66",
  muted: "#8A938F",
  border: "#E4E9E5",
  caution: "#D99A24",
  cautionBg: "#FFF6DF",
  critical: "#D9534F",
  criticalBg: "#FDECEC",
};

const plans = [
  {
    name: "Symptom Analysis",
    description:
      "Analyse user-entered symptoms using NLP and AI models to identify possible health conditions.",
    price: "High Priority",
    tag: "AI FEATURE",
  },
  {
    name: "Disease Risk Prediction",
    description:
      "Estimate disease risk using symptoms, medical history, laboratory reports, and clinical parameters.",
    price: "High Priority",
    tag: "PREDICTION",
  },
  {
    name: "Medical Report Explanation",
    description:
      "Interpret laboratory reports and provide simplified explanations of medical terms and abnormal values.",
    price: "High Priority",
    tag: "REPORT ANALYSIS",
  },
];

const faqs = [
  {
    question: "What is MediCare?",
    answer:
      "MediCare is an Intelligent Clinical Decision Support System that uses AI and Explainable AI to assist patients and healthcare professionals with medical information and decision support.",
  },
  {
    question: "What can MediCare help me with?",
    answer:
      "The system supports symptom analysis, disease risk prediction, medical report explanation, medicine information, drug interaction detection, and evidence-based medical recommendations.",
  },
  {
    question: "Does MediCare replace a doctor?",
    answer:
      "No. The system is designed to support clinical decision making and must not replace professional medical diagnosis or treatment.",
  },
  {
    question: "How does MediCare explain AI predictions?",
    answer:
      "MediCare uses Explainable AI techniques such as SHAP to identify influential features and provide transparent explanations for disease predictions.",
  },
];


// --- Logo ---
// What it does: Renders responsive SVG/icon branding badge for MediCare.
// Why it's structured this way: Supports dynamic light and dark theme styling via props.
// Parameters & Returns: { dark } -> Brand header element.
// ------------------------------------------------------------------------------
function Logo({ dark = false }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#0FA37F] text-white">
        <HeartPulse size={20} strokeWidth={2.5} />
      </div>

      <span
        className={`text-xl font-black tracking-[-0.04em] ${
          dark ? "text-white" : "text-[#123D32]"
        }`}
      >
        medicare<span className="text-[#087F68]">.</span>
      </span>
    </div>
  );
}

function Pill({ children, dark = false }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] ${
        dark
          ? "border-white/15 bg-white/5 text-white/70"
          : "border-[#E4E9E5] bg-[#F4FBF8] text-[#5F6B66]"
      }`}
    >
      {children}
    </span>
  );
}

function ArrowButton({ children, dark = false }) {
  return (
    <button
      className={`group inline-flex items-center gap-3 rounded-full px-5 py-3 text-sm font-bold transition ${
        dark
          ? "bg-[#087F68] text-white hover:bg-[#123D32]"
          : "bg-[#123D32] text-white hover:bg-[#087F68]"
      }`}
    >
      {children}

      <span
        className={`flex h-7 w-7 items-center justify-center rounded-full transition group-hover:translate-x-0.5 ${
          dark
            ? "bg-[#123D32] text-white"
            : "bg-white text-[#123D32]"
        }`}
      >
        <ArrowUpRight size={14} />
      </span>
    </button>
  );
}

/* =========================================================
   NEW HERO VISUAL BLOCK
========================================================= */

function HealthInsightVisual() {
  return (
    <div className="relative h-[520px] w-full max-w-[580px]">

      {/* Soft mint glow */}
      <div className="absolute left-1/2 top-1/2 h-[390px] w-[390px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#E8F7F2] blur-3xl" />

      {/* =====================================================
          MAIN VISUAL
      ===================================================== */}

      <div className="absolute left-1/2 top-1/2 h-[380px] w-[300px] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-[30px] bg-[#DCEFE8] shadow-[0_25px_70px_rgba(18,61,50,0.12)]">

        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#F4FBF8] via-[#E3F1EC] to-[#CDE5DC]" />

        {/* subtle circles */}
        <div className="absolute -left-20 top-12 h-40 w-40 rounded-full bg-white/40 blur-2xl" />
        <div className="absolute -right-16 bottom-10 h-44 w-44 rounded-full bg-[#0FA37F]/10 blur-2xl" />

        {/* =================================================
            STYLISED HEALTHCARE PERSON
        ================================================= */}

        <div className="absolute bottom-0 left-1/2 h-[325px] w-[185px] -translate-x-1/2">

          {/* Head */}
          <div className="absolute left-[48px] top-0 h-[82px] w-[82px] rounded-full bg-[#B8A08A]" />

          {/* Hair */}
          <div className="absolute left-[46px] top-[-3px] h-[46px] w-[85px] rounded-t-[45px] bg-[#4E4036]" />

          {/* Ear */}
          <div className="absolute left-[43px] top-[35px] h-5 w-4 rounded-full bg-[#B8A08A]" />

          {/* Neck */}
          <div className="absolute left-[70px] top-[73px] h-[42px] w-[38px] rounded-b-xl bg-[#B8A08A]" />

          {/* White coat */}
          <div className="absolute bottom-0 left-[15px] h-[235px] w-[155px] rounded-t-[48px] bg-white shadow-sm" />

          {/* Green clothing */}
          <div className="absolute bottom-0 left-[15px] h-[235px] w-[72px] rounded-t-[48px] bg-[#087F68]" />

          {/* Inner shirt */}
          <div className="absolute left-[73px] top-[112px] h-[155px] w-[72px] bg-white" />

          {/* Collar */}
          <div className="absolute left-[71px] top-[105px] h-5 w-14 rotate-[18deg] bg-[#F4FBF8]" />

          {/* =================================================
              STETHOSCOPE
          ================================================= */}

          <div className="absolute left-[83px] top-[120px] h-[120px] w-[62px] rounded-b-[40px] border-[5px] border-[#0FA37F] border-t-0" />

          <div className="absolute left-[108px] top-[225px] h-7 w-7 rounded-full border-4 border-[#0FA37F] bg-white" />

          {/* =================================================
              TABLET
          ================================================= */}

          <div className="absolute left-[28px] top-[178px] h-[68px] w-[118px] rotate-[-8deg] rounded-xl bg-[#123D32] shadow-xl">

            <div className="absolute inset-[7px] rounded-md bg-[#E8F7F2]">

              <div className="ml-3 mt-3 h-2 w-14 rounded-full bg-[#0FA37F]" />

              <div className="ml-3 mt-2 h-2 w-10 rounded-full bg-[#123D32]/20" />

              <div className="ml-3 mt-4 h-2 w-20 rounded-full bg-[#123D32]/15" />

              <div className="ml-3 mt-4 h-1.5 w-12 rounded-full bg-[#087F68]/30" />

            </div>

          </div>

        </div>

        {/* Decorative UI detail */}
        <div className="absolute right-5 top-6 h-8 w-8 rounded-full border border-[#0FA37F]/30 bg-white/60" />

        <div className="absolute bottom-7 right-5 h-2.5 w-2.5 rounded-full bg-[#0FA37F]" />

      </div>

      {/* =====================================================
          SHIELD BADGE
      ===================================================== */}

      <div className="absolute right-[92px] top-[45px] z-20 flex h-11 w-11 items-center justify-center rounded-full bg-[#0FA37F] text-white shadow-lg">
        <ShieldCheck size={20} />
      </div>

      {/* =====================================================
          HEALTH SCORE CARD
      ===================================================== */}

      <div className="absolute left-0 top-[95px] z-30 w-[245px] rounded-[22px] border border-[#E4E9E5] bg-white p-5 shadow-[0_18px_45px_rgba(18,61,50,0.14)] dark:border-white/10 dark:bg-[#16221E]">

        <p className="text-[11px] font-bold text-[#123D32]">
          Health Score
        </p>

        <div className="mt-3 flex items-center gap-3">

          {/* score circle */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full border-[4px] border-[#0FA37F] text-sm font-black text-[#087F68]">
            82
          </div>

          <div>
            <p className="text-lg font-black text-[#123D32]">
              82 /100
            </p>

            <p className="text-[10px] font-semibold text-[#087F68]">
              Good
            </p>
          </div>

        </div>

        <div className="mt-4 space-y-1.5">

          <p className="text-[9px] font-medium text-[#5F6B66]">
            Risk Overview
          </p>

          <p className="text-[9px] text-[#5F6B66]">
            Diabetes Risk — Low
          </p>

          <p className="text-[9px] text-[#5F6B66]">
            Hypertension Risk — Medium
          </p>

          <p className="text-[9px] text-[#5F6B66]">
            Heart Disease Risk — Low
          </p>

        </div>

        <button className="mt-3 text-[9px] font-bold text-[#087F68]">
          View Full Report →
        </button>

      </div>

      {/* =====================================================
          AI INSIGHT CARD
      ===================================================== */}

      <div className="absolute bottom-[40px] right-0 z-30 w-[245px] rounded-[22px] border border-[#E4E9E5] bg-white p-5 shadow-[0_18px_45px_rgba(18,61,50,0.14)] dark:border-white/10 dark:bg-[#16221E]">

        <div className="flex items-center gap-2">

          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#E8F7F2] text-[#0FA37F]">
            <Activity size={13} />
          </div>

          <p className="text-[11px] font-bold text-[#123D32]">
            AI Insight
          </p>

        </div>

        <p className="mt-3 text-[9px] leading-4 text-[#5F6B66]">
          Your HbA1c levels are slightly elevated. Lifestyle changes and
          regular monitoring are recommended.
        </p>

        <button className="mt-3 text-[9px] font-bold text-[#087F68]">
          Know more →
        </button>

      </div>

    </div>
  );
}

function PlanMiniCard({ title, value, icon: Icon }) {
  return (
    <div className="rounded-[24px] border border-[#E4E9E5] bg-white p-5 dark:border-white/10 dark:bg-white/5">

      <div className="flex items-start justify-between">

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E8F7F2] text-[#0FA37F]">
          <Icon size={18} />
        </div>

        <ArrowUpRight
          size={17}
          className="text-[#123D32]/30"
        />

      </div>

      <p className="mt-8 text-xs font-semibold uppercase tracking-[0.14em] text-[#5F6B66]/70">
        {title}
      </p>

      <p className="mt-1 text-2xl font-black tracking-[-0.04em]">
        {value}
      </p>

    </div>
  );
}

// --- LandingPage ---
// What it does: Primary landing page displaying hero section, interactive clinical preview cards, feature breakdown, and FAQs.
// Why it's structured this way: Assembles modular presentation sections and drives interactive theme toggle and mobile navigation drawer.
// Parameters & Returns: Props (none) -> Landing page JSX hierarchy.
// ------------------------------------------------------------------------------
export default function LandingPage() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useTheme();

  const handleProjectClick = (event) => {
    event.preventDefault();

    const aboutSection = document.getElementById("about");

    if (aboutSection) {
      aboutSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }

    setMobileOpen(false);
  };

  useEffect(() => {
    const root = document.documentElement;
    const previousBehavior = root.style.scrollBehavior;

    root.style.scrollBehavior = "smooth";

    return () => {
      root.style.scrollBehavior = previousBehavior;
    };
  }, []);

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#FFFEFC] text-[#123D32] dark:bg-[#0B1210] dark:text-white">

      {/* =========================================================
          NAVBAR
      ========================================================= */}

      <header className="fixed inset-x-0 top-0 z-[100] border-b border-[#E4E9E5]/80 bg-white/95 backdrop-blur-xl dark:border-white/10 dark:bg-[#0B1210]/95">

        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-5 py-5 lg:px-10">

          <Logo />

          <nav className="hidden items-center gap-8 lg:flex">

            {[
              ["Features", "#plans"],
              ["How it works", "#how-it-works"],
              ["Resources", "#resources"],
              ["Project", "#about"],
            ].map(([name, link]) => (

              <a
                key={name}
                href={link}
                onClick={
                  name === "Project"
                    ? handleProjectClick
                    : undefined
                }
                className="text-sm font-semibold text-[#5F6B66] transition hover:text-[#123D32] dark:text-white/60 dark:hover:text-white"
              >
                {name}
              </a>

            ))}

          </nav>

          <div className="hidden items-center gap-3 sm:flex">

            <button
              onClick={toggleTheme}
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
              className="flex h-11 w-11 items-center justify-center rounded-full border border-[#E4E9E5] bg-white text-[#123D32] transition hover:bg-[#F4FBF8] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <button
              onClick={() => navigate("/login")}
              className="rounded-full px-5 py-3 text-sm font-bold text-[#5F6B66] transition hover:text-[#123D32] dark:text-white/70 dark:hover:text-white"
            >
              Sign in
            </button>

            <button
              onClick={() => navigate("/login")}
              className="group inline-flex items-center gap-3 rounded-full bg-[#123D32] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#087F68]"
            >
              Get started

              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-[#123D32] transition group-hover:translate-x-0.5">
                <ArrowUpRight size={14} />
              </span>
            </button>

          </div>

          <div className="flex items-center gap-2 lg:hidden">
            <button
              onClick={toggleTheme}
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
              className="flex h-11 w-11 items-center justify-center rounded-full border border-[#E4E9E5] bg-white text-[#123D32] transition hover:bg-[#F4FBF8] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="flex h-11 w-11 items-center justify-center rounded-full bg-[#123D32] text-white lg:hidden"
          >
            {mobileOpen ? (
              <X size={20} />
            ) : (
              <Menu size={20} />
            )}
            </button>
          </div>

        </div>

        {mobileOpen && (

          <div className="border-t border-[#E4E9E5] bg-white/95 px-5 py-6 backdrop-blur-xl lg:hidden dark:border-white/10 dark:bg-[#0B1210]/95">

            <div className="flex flex-col gap-5">

              {[
                ["Features", "#plans"],
                ["How it works", "#how-it-works"],
                ["Resources", "#resources"],
                ["Project", "#about"],
              ].map(([name, link]) => (

                <a
                  key={name}
                  href={link}
                  onClick={(event) => {

                    if (name === "Project") {
                      handleProjectClick(event);
                    } else {
                      setMobileOpen(false);
                    }

                  }}
                  className="text-lg font-bold"
                >
                  {name}
                </a>

              ))}

              <button
                onClick={() => {
                  setMobileOpen(false);
                  navigate("/login");
                }}
                className="rounded-full bg-[#087F68] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#123D32]"
              >
                Get started
              </button>

            </div>

          </div>

        )}

      </header>

      {/* =========================================================
          HERO
      ========================================================= */}

      <section
        id="home"
        className="relative scroll-mt-24 pt-16 lg:min-h-screen lg:pt-8"
      >

        <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-8 px-5 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:px-10 lg:py-8">

          <div className="flex flex-col justify-center">

            

            <h1 className="max-w-4xl text-[clamp(4rem,8vw,8.5rem)] font-black leading-[0.82] tracking-[-0.075em]">

              Smarter

              <br />

              <span className="text-[#5F6B66] dark:text-white/60">
                insights.
              </span>{" "}

              <span className="text-[#087F68]">
                Less
              </span>

              <br />

              uncertainty.

            </h1>

            <p className="mt-9 max-w-xl text-lg leading-7 text-[#5F6B66] lg:text-xl dark:text-white/60">
              Analyse symptoms, understand medical reports, predict disease
              risk, and explore evidence-based healthcare information through
              one intelligent clinical decision-support system.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-4">

              <ArrowButton>
                Explore system features
              </ArrowButton>

              <button className="group flex items-center gap-3 rounded-full border border-[#E4E9E5] bg-white px-4 py-3 text-sm font-bold text-[#123D32] transition hover:border-[#0FA37F] hover:bg-[#F4FBF8] hover:text-[#087F68] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">

                How it works

                <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[#E4E9E5] transition group-hover:bg-[#123D32] group-hover:text-white">

                  <ArrowRight size={14} />

                </span>

              </button>

            </div>

            <div className="mt-12 flex flex-wrap items-center gap-x-8 gap-y-4 border-t border-[#E4E9E5] pt-7">

              <div>

                <p className="text-2xl font-black tracking-tight">
                  AI + XAI
                </p>

                <div className="mt-1 flex gap-0.5 text-[#087F68]">

                  {[1, 2, 3, 4, 5].map((n) => (

                    <Star
                      key={n}
                      size={12}
                      fill="currentColor"
                    />

                  ))}

                </div>

              </div>

              <div className="h-10 w-px bg-[#123D32]/10" />

              <div>

                <p className="text-2xl font-black tracking-tight">
                  3 roles
                </p>

                <p className="text-xs text-[#5F6B66]/70">
                  Patient · Doctor · Admin
                </p>

              </div>

              <div className="h-10 w-px bg-[#123D32]/10" />

              <div>

                <p className="text-2xl font-black tracking-tight">
                  10+
                </p>

                <p className="text-xs text-[#5F6B66]/70">
                  Core features
                </p>

              </div>

            </div>

          </div>

          {/* =====================================================
              HERO RIGHT SIDE
          ===================================================== */}

          <div className="relative flex items-center justify-center lg:min-h-[560px]">

            <div className="absolute right-5 top-4 h-72 w-72 rounded-full bg-[#087F68] opacity-15 blur-3xl" />

            <div className="relative w-full max-w-[580px]">

              {/* THIS IS THE NEW CODED BLOCK */}
              <HealthInsightVisual />

              <div className="mt-4 grid grid-cols-2 gap-4">

                <PlanMiniCard
                  title="Symptom analysis"
                  value="Available"
                  icon={Stethoscope}
                />

                <PlanMiniCard
                  title="Report analysis"
                  value="AI powered"
                  icon={FileText}
                />

              </div>

              {/* Bottom AI generated toast */}

              <div className="absolute -bottom-8 -left-6 hidden rounded-2xl border border-[#E4E9E5] bg-white p-4 shadow-xl sm:block dark:border-white/10 dark:bg-[#16221E]">

                <div className="flex items-center gap-3">

                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#087F68]">

                    <Check size={19} />

                  </div>

                  <div>

                    <p className="text-xs font-bold">
                      AI insight generated
                    </p>

                    <p className="text-[10px] text-[#5F6B66]/70">
                      Based on clinical input and available data
                    </p>

                  </div>

                </div>

              </div>

            </div>

          </div>

        </div>

        {/* =========================================================
            TICKER
        ========================================================= */}

        <div className="border-y border-[#E4E9E5] bg-white dark:border-white/10 dark:bg-[#101A17]">

          <div className="mx-auto flex max-w-[1400px] items-center gap-8 overflow-hidden px-5 py-4 lg:px-10">

            {[
              "Analyse symptoms",
              "Predict disease risk",
              "Explain reports",
              "Check medicines",
              "Explain AI decisions",
              "Manage health records",
            ].map((item, index) => (

              <React.Fragment key={item}>

                <span className="whitespace-nowrap text-xs font-black uppercase tracking-[0.15em] text-[#5F6B66]">
                  {item}
                </span>

                {index !== 5 && (

                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#087F68]" />

                )}

              </React.Fragment>

            ))}

          </div>

        </div>

      </section>

      {/* =========================================================
          ABOUT / PROJECT
      ========================================================= */}

      <section
        id="about"
        className="mx-auto max-w-[1400px] px-5 py-24 lg:min-h-[820px] lg:px-10 lg:py-32"
      >

        <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr]">

          <div>

            <Pill>
              Why MediCare
            </Pill>

            <h2 className="mt-6 max-w-xl text-5xl font-black leading-[0.92] tracking-[-0.06em] md:text-6xl">

              Healthcare decisions should feel{" "}

              <span className="text-[#5F6B66] dark:text-white/60">
                human.
              </span>

            </h2>

          </div>

          <div className="flex items-end">

            <p className="max-w-2xl text-xl leading-8 text-[#5F6B66]">
              Medical information can be complex. MediCare combines AI,
              Explainable AI, and evidence-based knowledge to make healthcare
              information easier to understand and support informed clinical
              decisions.
            </p>

          </div>

        </div>

        <div className="mt-16 grid gap-4 md:grid-cols-2 lg:grid-cols-4">

          {[
            {
              number: "01",
              icon: Activity,
              title: "Analyse symptoms",
              text: "Use natural language symptom input and AI models to identify possible health conditions.",
            },
            {
              number: "02",
              icon: Stethoscope,
              title: "Predict disease risk",
              text: "Estimate disease risk using symptoms, clinical parameters, and available medical history.",
            },
            {
              number: "03",
              icon: ShieldCheck,
              title: "Explain medical reports",
              text: "Interpret laboratory reports and present simplified explanations of abnormal values and medical terms.",
            },
            {
              number: "04",
              icon: Users,
              title: "Improve transparency",
              text: "Generate SHAP-based explanations and evidence-backed information for AI-supported recommendations.",
            },
          ].map((feature) => {

            const Icon = feature.icon;

            return (
              <div
                key={feature.number}
                className="group rounded-[30px] border border-[#E4E9E5] bg-[#123D32] p-7 text-white shadow-[0_18px_45px_rgba(18, 61, 50, 0.06)] transition duration-300 hover:-translate-y-1 hover:bg-[#087F68]"
              >

                <div className="flex items-start justify-between">

                  <span className="text-xs font-bold text-white/55">
                    {feature.number}
                  </span>

                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#E8F7F2] text-[#0FA37F] transition duration-300 group-hover:scale-105">

                    <Icon size={18} />

                  </div>

                </div>

                <h3 className="mt-14 text-2xl font-black tracking-[-0.04em]">
                  {feature.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-white/60">
                  {feature.text}
                </p>

                <div className="mt-8 border-t border-white/10 pt-5">

                  <span className="text-xs font-bold uppercase tracking-[0.15em] text-[#E4E9E5]">
                    Learn more →
                  </span>

                </div>

              </div>
            );

          })}

        </div>

      </section>

      {/* =========================================================
          PLANS / CORE FEATURES
      ========================================================= */}

      <section
        id="plans"
        className="scroll-mt-24 bg-[#123D32] px-5 py-20 text-white lg:px-10 lg:py-24"
      >

        <div className="mx-auto max-w-[1400px]">

          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">

            <div>

              <Pill dark>
                Core features
              </Pill>

              <h2 className="mt-6 max-w-2xl text-5xl font-black leading-[0.9] tracking-[-0.06em] md:text-7xl">

                Explore the
                <br />

                <span className="text-[#E4E9E5]">
                  MediCare system.
                </span>

              </h2>

            </div>

            <div className="flex items-end">

              <p className="max-w-xl text-lg leading-7 text-white/60">
                MediCare integrates AI, Explainable AI, medical knowledge
                retrieval, and digital health records to support patients,
                doctors, and administrators.
              </p>

            </div>

          </div>

          <div className="mt-12 grid gap-4 lg:grid-cols-3">

            {plans.map((plan, index) => (

              <div
                key={plan.name}
                className={`group rounded-[32px] p-7 transition ${
                  index === 0
                    ? "bg-[#087F68] text-white"
                    : index === 1
                    ? "border border-white/10 bg-white/5 hover:bg-white/10"
                    : "bg-[#FFFEFC] text-[#123D32] hover:bg-[#E4E9E5]"
                }`}
              >

                <div className="flex items-center justify-between">

                  <span
                    className={`rounded-full px-3 py-1.5 text-[9px] font-black tracking-[0.15em] ${
                      index === 0
                        ? "bg-[#123D32] text-white"
                        : index === 1
                        ? "bg-white/10 text-white/70"
                        : "bg-[#123D32] text-white"
                    }`}
                  >
                    {plan.tag}
                  </span>

                  <span
                    className={`text-sm font-bold ${
                      index === 0
                        ? "text-white/45"
                        : index === 1
                        ? "text-white/40"
                        : "text-[#5F6B66]"
                    }`}
                  >
                    0{index + 1}
                  </span>

                </div>

                <h3
                  className={`mt-14 text-3xl font-black tracking-[-0.05em] ${
                    index === 2 ? "text-[#123D32]" : ""
                  }`}
                >
                  {plan.name}
                </h3>

                <p
                  className={`mt-4 min-h-[72px] text-sm leading-6 ${
                    index === 0
                      ? "text-white/65"
                      : index === 1
                      ? "text-white/60"
                      : "text-[#5F6B66]"
                  }`}
                >
                  {plan.description}
                </p>

                <div
                  className={`mt-7 border-t pt-5 ${
                    index === 0
                      ? "border-white/25"
                      : index === 1
                      ? "border-white/10"
                      : "border-[#E4E9E5]"
                  }`}
                >

                  <div className="flex items-center justify-between">

                    <div>

                      <p
                        className={`text-[9px] font-bold uppercase tracking-[0.15em] ${
                          index === 2
                            ? "text-[#5F6B66]"
                            : "text-white/45"
                        }`}
                      >
                        Priority
                      </p>

                      <p
                        className={`mt-1 text-xl font-black ${
                          index === 2
                            ? "text-[#123D32]"
                            : ""
                        }`}
                      >
                        {plan.price}
                      </p>

                    </div>

                    <button
                      className={`flex h-12 w-12 items-center justify-center rounded-full transition group-hover:rotate-45 ${
                        index === 0
                          ? "bg-[#123D32] text-white"
                          : index === 1
                          ? "bg-white text-[#123D32]"
                          : "bg-[#123D32] text-white"
                      }`}
                    >

                      <ArrowUpRight size={19} />

                    </button>

                  </div>

                </div>

              </div>

            ))}

          </div>

        </div>

      </section>

      {/* =========================================================
          HOW IT WORKS
      ========================================================= */}

      <section
        id="how-it-works"
        className="scroll-mt-24 mx-auto max-w-[1400px] px-5 py-24 lg:px-10 lg:py-32"
      >

        <div className="grid items-center gap-16 lg:grid-cols-2">

          <div>

            <Pill>
              How it works
            </Pill>

            <h2 className="mt-7 max-w-xl text-5xl font-black leading-[0.9] tracking-[-0.06em] md:text-7xl">

              Three stages.
              <br />

              <span className="text-[#087F68]">
                One connected
              </span>

              <br />

              workflow.

            </h2>

            <p className="mt-8 max-w-lg text-lg leading-7 text-[#123D32]/50">
              MediCare connects patients, healthcare professionals, and
              administrators through a structured clinical decision-support
              workflow.
            </p>

            <div className="mt-8">

              <ArrowButton>
                Explore MediCare
              </ArrowButton>

            </div>

          </div>

          <div className="space-y-3">

            {[
              {
                no: "01",
                title: "Patient input",
                text: "Patients can register, enter symptoms, upload laboratory reports, and access AI-generated health insights.",
              },
              {
                no: "02",
                title: "AI-assisted analysis",
                text: "The system analyses symptoms, predicts disease risk, explains reports, detects drug interactions, and retrieves medical evidence.",
              },
              {
                no: "03",
                title: "Clinical decision support",
                text: "Doctors can review patient history, validate AI recommendations, and record clinical observations before making decisions.",
              },
            ].map((step) => (

              <div
                key={step.no}
                className="group rounded-[28px] border border-[#E4E9E5] bg-white p-6 transition hover:bg-[#123D32] hover:text-white dark:border-white/10 dark:bg-white/5"
              >

                <div className="flex gap-6">

                  <span className="pt-1 text-xs font-black text-[#5F6B66] group-hover:text-white/25">
                    {step.no}
                  </span>

                  <div className="flex-1">

                    <div className="flex items-center justify-between">

                      <h3 className="text-xl font-black tracking-[-0.03em]">
                        {step.title}
                      </h3>

                      <ArrowUpRight
                        size={18}
                        className="text-[#123D32]/20 transition group-hover:text-[#E4E9E5]"
                      />

                    </div>

                    <p className="mt-2 max-w-lg text-sm leading-6 text-[#5F6B66] group-hover:text-white/60">
                      {step.text}
                    </p>

                  </div>

                </div>

              </div>

            ))}

          </div>

        </div>

      </section>

      {/* =========================================================
          CTA
      ========================================================= */}

      <section className="px-5 pb-24 lg:px-10 lg:pb-32">

        <div className="mx-auto max-w-[1400px] overflow-hidden rounded-[40px] border border-[#E4E9E5] bg-[#E8F7F2] dark:border-white/10 dark:bg-[#10251F]">

          <div className="relative grid min-h-[480px] items-center gap-10 px-7 py-16 lg:grid-cols-[1.2fr_0.8fr] lg:px-16">

            <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full border-[60px] border-[#087F68]/10" />

            <div className="absolute -bottom-40 right-20 h-96 w-96 rounded-full border-[45px] border-[#087F68]/10" />

            <div className="relative">

              <Pill>
                Intelligent healthcare support
              </Pill>

              <h2 className="mt-7 max-w-4xl text-5xl font-black leading-[0.88] tracking-[-0.07em] md:text-7xl lg:text-8xl">

                Understand your health.
                <br />

                Understand the evidence.
                <br />

                <span className="text-[#123D32]/30">
                  Make informed decisions.
                </span>

              </h2>

              <div className="mt-9">

                <button className="group inline-flex items-center gap-4 rounded-full bg-[#123D32] px-6 py-4 text-sm font-bold text-white shadow-lg shadow-[rgba(18,61,50,0.06)]">

                  Explore MediCare

                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0FA37F] text-white transition group-hover:rotate-45">

                    <ArrowUpRight size={15} />

                  </span>

                </button>

              </div>

            </div>

            <div className="relative hidden justify-end lg:flex">

              <div className="w-[340px] rotate-3 rounded-[34px] bg-[#123D32] p-6 text-white shadow-2xl">

                <div className="flex items-center justify-between">

                  <span className="text-xs font-bold uppercase tracking-[0.15em] text-white/55">
                    MediCare Dashboard
                  </span>

                  <HeartPulse
                    className="text-[#087F68]"
                    size={20}
                  />

                </div>

                <div className="mt-16">

                  <p className="text-xs uppercase tracking-[0.15em] text-white/45">
                    Latest AI insight
                  </p>

                  <p className="mt-2 text-3xl font-black tracking-[-0.04em]">
                    Disease Risk Prediction
                  </p>

                  <p className="mt-1 text-sm text-white/55">
                    AI-supported clinical assessment
                  </p>

                </div>

                <div className="mt-10 grid grid-cols-2 gap-2">

                  <div className="rounded-2xl bg-white/5 p-4">

                    <p className="text-[9px] uppercase text-white/45">
                      AI Features
                    </p>

                    <p className="mt-1 text-sm font-bold">
                      4+ modules
                    </p>

                  </div>

                  <div className="rounded-2xl bg-white/5 p-4">

                    <p className="text-[9px] uppercase text-white/45">
                      Explainability
                    </p>

                    <p className="mt-1 text-sm font-bold">
                      SHAP
                    </p>

                  </div>

                </div>

              </div>

            </div>

          </div>

        </div>

      </section>

      {/* =========================================================
          FAQ
      ========================================================= */}

      <section
        id="resources"
        className="scroll-mt-24 mx-auto max-w-[1100px] px-5 pb-24 lg:pb-32"
      >

        <div className="text-center">

          <Pill>
            Frequently asked questions
          </Pill>

          <h2 className="mx-auto mt-6 max-w-3xl text-5xl font-black leading-[0.9] tracking-[-0.06em] md:text-7xl">

            Let's make
            <br />

            healthcare{" "}

            <span className="text-[#087F68]">
              clear.
            </span>

          </h2>

        </div>

        <div className="mt-14">

          {faqs.map((faq, index) => {

            const isOpen = openFaq === index;

            return (
              <div
                key={faq.question}
                className="border-b border-[#E4E9E5] dark:border-white/10"
              >

                <button
                  onClick={() =>
                    setOpenFaq(
                      isOpen
                        ? null
                        : index
                    )
                  }
                  className="flex w-full items-center justify-between gap-5 py-7 text-left"
                >

                  <span className="text-xl font-black tracking-[-0.03em] md:text-2xl">
                    {faq.question}
                  </span>

                  <span
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[#E4E9E5] transition ${
                      isOpen
                        ? "rotate-45 bg-[#087F68] text-white"
                        : ""
                    }`}
                  >

                    <Plus size={18} />

                  </span>

                </button>

                <div
                  className={`grid transition-all duration-300 ${
                    isOpen
                      ? "grid-rows-[1fr] pb-7 opacity-100"
                      : "grid-rows-[0fr] opacity-0"
                  }`}
                >

                  <div className="overflow-hidden">

                    <p className="max-w-2xl text-base leading-7 text-[#123D32]/50 dark:text-white/50">
                      {faq.answer}
                    </p>

                  </div>

                </div>

              </div>
            );

          })}

        </div>

      </section>

      {/* =========================================================
          FOOTER
      ========================================================= */}

      <footer className="bg-[#123D32] px-5 py-12 text-white lg:px-10">

        <div className="mx-auto max-w-[1400px]">

          <div className="grid gap-12 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">

            <div>

              <Logo dark />

              <p className="mt-5 max-w-sm text-sm leading-6 text-white/55">
                Making healthcare information easier to understand through
                AI-assisted analysis, Explainable AI, and evidence-based
                medical knowledge.
              </p>

            </div>

            <div>

              <p className="text-xs font-bold uppercase tracking-[0.15em] text-white/45">
                Explore
              </p>

              <div className="mt-5 space-y-3">

                <a
                  href="#plans"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  System features
                </a>

                <a
                  href="#how-it-works"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  How it works
                </a>

                <a
                  href="#resources"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Resources
                </a>

              </div>

            </div>

            <div>

              <p className="text-xs font-bold uppercase tracking-[0.15em] text-white/45">
                Company
              </p>

              <div className="mt-5 space-y-3">

                <a
                  href="#about"
                  onClick={handleProjectClick}
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Project
                </a>

                <a
                  href="#"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Technology
                </a>

                <a
                  href="#"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Team
                </a>

              </div>

            </div>

            <div>

              <p className="text-xs font-bold uppercase tracking-[0.15em] text-white/45">
                Legal
              </p>

              <div className="mt-5 space-y-3">

                <a
                  href="#"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Security
                </a>

                <a
                  href="#"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Safety
                </a>

                <a
                  href="#"
                  className="block text-sm text-white/60 hover:text-white"
                >
                  Documentation
                </a>

              </div>

            </div>

          </div>

          <div className="mt-14 flex flex-col justify-between gap-4 border-t border-white/10 pt-6 text-xs text-white/45 md:flex-row">

            <p>
              © 2026 MediCare. All rights reserved.
            </p>

            <p>
              AI-generated healthcare information is intended for decision
              support and should be verified by qualified healthcare
              professionals.
            </p>

          </div>

        </div>

      </footer>

    </main>
  );
}
