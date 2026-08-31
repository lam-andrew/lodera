import { NavLink } from "react-router-dom";

import { APP_NAME } from "@/config/branding";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  to?: string;
  /** Stories not yet built are listed but visibly inert, so the nav shows where things land. */
  soon?: boolean;
  icon: JSX.Element;
}

const icon = (d: string) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    className="h-4 w-4 flex-none opacity-80"
  >
    <path d={d} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: "Portfolio",
    items: [
      {
        label: "Overview",
        to: "/",
        icon: icon("M4 13h7V4H4v9Zm9 7h7v-9h-7v9ZM4 20h7v-4H4v4Zm9-11h7V4h-7v5Z"),
      },
      { label: "Holdings", to: "/holdings", icon: icon("M4 6h16M4 12h16M4 18h10") },
    ],
  },
  {
    title: "Risk & Exposure",
    items: [
      { label: "Correlation", to: "/correlation", icon: icon("M3 3v18h18M3 15h18M9 3v18M15 3v18") },
      { label: "Concentration", to: "/concentration", icon: icon("M12 3a9 9 0 1 0 9 9h-9V3Z") },
      { label: "Drawdown", to: "/drawdown", icon: icon("M3 7l5 6 4-3 4 5 5-9") },
    ],
  },
  {
    title: "Insights",
    items: [{ label: "Filings Q&A", soon: true, icon: icon("M4 4h11l5 5v11H4V4Zm4 8h8M8 16h5") }],
  },
  {
    title: "Reference",
    items: [
      {
        label: "How this is calculated",
        to: "/methodology",
        icon: icon("M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Zm0 5v5m0 3h.01"),
      },
    ],
  },
];

const base =
  "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13.5px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <div className="flex items-center gap-2.5 px-1.5 pt-1">
        <span
          className="grid h-8 w-8 flex-none place-items-center rounded-lg text-white"
          style={{ background: "linear-gradient(150deg, var(--accent), #7c5cff)" }}
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            className="h-[17px] w-[17px]"
          >
            <path d="M4 19V5M4 15l4-4 3 3 5-6 4 4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <span className="flex flex-col leading-tight">
          <span className="text-[15px] font-semibold tracking-tight">{APP_NAME}</span>
          <span className="text-[10.5px] text-faint">Risk intelligence</span>
        </span>
      </div>

      <nav className="flex flex-col gap-5">
        {GROUPS.map((group) => (
          <div key={group.title} className="flex flex-col gap-0.5">
            <span className="px-2.5 pb-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.13em] text-faint">
              {group.title}
            </span>
            {group.items.map((item) =>
              item.soon === true || item.to === undefined ? (
                <span
                  key={item.label}
                  className={cn(base, "cursor-default text-muted-foreground opacity-55")}
                >
                  {item.icon}
                  {item.label}
                  <span className="ml-auto rounded-full border border-border px-1.5 font-mono text-[9px] tracking-wider text-faint">
                    SOON
                  </span>
                </span>
              ) : (
                <NavLink
                  key={item.label}
                  to={item.to}
                  end={item.to === "/"}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      base,
                      isActive
                        ? "bg-accent/10 font-medium text-accent"
                        : "text-muted-foreground hover:bg-surface-2 hover:text-foreground",
                    )
                  }
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              ),
            )}
          </div>
        ))}
      </nav>
    </div>
  );
}
