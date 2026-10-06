import React from "react";

import {
  Link,
  useLocation,
} from "react-router-dom";

import {
  LayoutDashboard,
  UsersRound,
  FileText,
  Sparkles,
  Pill,
  ClipboardList,
  BookOpen,
  Settings,
  LogIn,
  Heart,
} from "lucide-react";

import { useTheme } from "../ThemeContext";


// =========================================================
// ROUTES
// =========================================================

const ROUTES = {
  dashboard: "/doctor/dashboard",
  patients: "/doctor/patients",
  reports: "/doctor/reports",
  aiInsights: "/doctor/insights",
  medications: "/doctor/medications",
  clinicalNotes: "/doctor/clinical-notes",
  medicalKnowledge: "/doctor/medical-knowledge",
  settings: "/doctor/dashboard?view=settings",
  logout: "/login",
};


// =========================================================
// NAVIGATION
// =========================================================

const navSections = [
  {
    title: "MAIN",

    items: [
      {
        label: "Dashboard",
        icon: LayoutDashboard,
        route: ROUTES.dashboard,
      },
    ],
  },

  {
    title: "CLINICAL",

    items: [
      {
        label: "Patients",
        icon: UsersRound,
        route: ROUTES.patients,
      },

      {
        label: "Reports",
        icon: FileText,
        route: ROUTES.reports,
      },

      {
        label: "AI Insights",
        icon: Sparkles,
        route: ROUTES.aiInsights,
      },

      {
        label: "Appointments",
        icon: Pill,
        route: ROUTES.medications,
      },

      {
        label: "Clinical Notes",
        icon: ClipboardList,
        route: ROUTES.clinicalNotes,
      },

      {
        label: "Medical Knowledge",
        icon: BookOpen,
        route: ROUTES.medicalKnowledge,
      },
    ],
  },
];


// =========================================================
// ACTIVE PATH
// =========================================================

function isActivePath(pathname, route, search = "") {
  const cleanPath = pathname.replace(/\/$/, "");
  const cleanRoute = route.replace(/\/$/, "").split("?")[0];

  if (route.includes("?view=settings")) {
    return cleanPath === cleanRoute && search.includes("view=settings");
  }

  return cleanPath === cleanRoute;
}


// =========================================================
// SIDEBAR
// =========================================================

export default function Sidebar() {
  const location = useLocation();
  const { isDark } = useTheme();

  return (
    <aside
      className={`
        fixed
        left-0
        top-0
        z-50

        flex
        h-screen
        w-[217px]
        min-w-[217px]
        max-w-[217px]
        flex-col
        overflow-hidden

        border-r

        ${"border-[var(--border)] bg-[var(--surface)]"
        }
      `}
    >

      {/* =====================================================
          LOGO
      ===================================================== */}

      <div className="shrink-0 px-5 pb-4 pt-4">

        <Link
          to={ROUTES.dashboard}
          className="flex items-center gap-4"
        >

          {/* Logo circle */}

          <div
            className="
              flex
              h-[46px]
              w-[46px]
              shrink-0
              items-center
              justify-center
              rounded-full
              bg-emerald-500
            "
          >
            <Heart
              size={18}
              strokeWidth={2.2}
              className="text-[#06231d]"
            />
          </div>

          {/* Brand */}

          <span
            className={`
              text-[21px]
              font-bold
              tracking-[-0.8px]

              ${"text-[var(--text)]"
              }
            `}
          >
            medicare
            <span className="text-emerald-500">
              .
            </span>
          </span>

        </Link>
      </div>


      {/* =====================================================
          NAVIGATION
      ===================================================== */}

      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-3 pb-2">

        <nav>
          <div className="space-y-4">

            {navSections.map((section) => (

              <div key={section.title}>

                {/* Section title */}

                <div
                  className={`
                  px-5
                  pb-3
                  text-[12px]
                  font-medium
                  tracking-[0.12em]

                  ${"text-[var(--muted)]"
                    }
                `}
                >
                  {section.title}
                </div>


                {/* Section items */}

                <div className="space-y-1">

                  {section.items.map((item) => {

                    const Icon = item.icon;

                    const active =
                      isActivePath(
                        location.pathname,
                        item.route,
                        location.search
                      );

                    return (
                      <Link
                        key={item.label}
                        to={item.route}
                        className={`
                        relative

                        flex
                        h-[46px]
                        w-full
                        items-center
                        gap-3

                        rounded-xl
                        px-4

                        text-[14px]

                        transition-all
                        duration-150

                        ${active
                            ? "bg-[var(--accent-surface)] font-medium text-[var(--text)]"
                            : "text-[var(--text-secondary)] hover:bg-[var(--card-hover)]"
                          }
                      `}
                      >

                        {/* Active indicator */}

                        {active && (
                          <span
                            className="
                            absolute
                            left-0
                            top-1/2

                            h-[26px]
                            w-[3px]

                            -translate-y-1/2

                            rounded-r-full

                            bg-emerald-400
                          "
                          />
                        )}


                        {/* Icon */}

                        <Icon
                          size={18}
                          strokeWidth={1.8}
                          className={
                            active
                              ? "text-[var(--accent)]"
                              : "text-[var(--muted)]"
                          }
                        />


                        {/* Label */}

                        <span className="truncate">
                          {item.label}
                        </span>

                      </Link>
                    );
                  })}

                </div>

              </div>
            ))}

          </div>
        </nav>

        {/* =====================================================
            BOTTOM AREA
        ===================================================== */}

        <div
          className={`
          shrink-0

          border-t

          px-3
          pb-0
          pt-4

          ${"border-[var(--border)]"
            }
        `}
        >

          {/* ===================================================
            SETTINGS
        =================================================== */}

          <Link
            to={ROUTES.settings}
            className={`
            relative

            flex
            h-[44px]
            w-full
            items-center
            gap-3

            rounded-xl
            px-4

            text-[14px]

            transition

            ${isActivePath(
              location.pathname,
              ROUTES.settings,
              location.search
            )
                ? "bg-[var(--accent-surface)] font-medium text-[var(--text)]"
                : "text-[var(--text-secondary)] hover:bg-[var(--card-hover)]"
              }
          `}
          >

            {/* Active indicator */}

            {isActivePath(
              location.pathname,
              ROUTES.settings,
              location.search
            ) && (
                <span
                  className="
                absolute
                left-0
                top-1/2

                h-[26px]
                w-[3px]

                -translate-y-1/2

                rounded-r-full

                bg-emerald-400
              "
                />
              )}


            <Settings
              size={18}
              strokeWidth={1.8}
            />

            <span>
              Settings
            </span>

          </Link>


          {/* ===================================================
            LOGOUT
        =================================================== */}

          <Link
            to={ROUTES.logout}
            className={`
            mt-1

            flex
            h-[44px]
            w-full
            items-center
            gap-3

            rounded-xl
            px-4

            text-[14px]

            transition

            ${"text-[var(--text-secondary)] hover:bg-[var(--card-hover)]"
              }
          `}
          >

            <LogIn
              size={18}
              strokeWidth={1.8}
            />

            <span>
              Logout
            </span>

          </Link>

        </div>


        {/* =====================================================
          DOCTOR PROFILE
      ===================================================== */}

        <div
          className={`
          mt-3

          shrink-0

          border-t

          px-4
          py-5

          ${"border-[var(--border)]"
            }
        `}
        >

          <div className="flex items-center gap-3">

            {/* Avatar */}

            <div
              className="
              flex
              h-[42px]
              w-[42px]
              shrink-0
              items-center
              justify-center

              rounded-full

              bg-[var(--accent-soft)]
              text-[var(--accent)]
            "
            >
              <UsersRound
                size={19}
                strokeWidth={1.7}
              />
            </div>


            {/* Doctor information */}

            <div className="min-w-0">

              <div
                className={`
                truncate

                text-[15px]
                font-semibold

                ${"text-[var(--text)]"
                  }
              `}
              >
                Dr. Olivia
              </div>


              <div
                className={`
                mt-1
                text-[13px]

                ${"text-[var(--muted)]"
                  }
              `}
              >
                Physician
              </div>

            </div>

          </div>

        </div>

      </div>

    </aside>
  );
}
