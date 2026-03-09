import { useState, useEffect, useRef } from "react";
import { Chart, ArcElement, DoughnutController, Tooltip } from "chart.js";
Chart.register(ArcElement, DoughnutController, Tooltip);

// ─── Mock fetch — replace with your real API call ─────────────────────────────
async function fetchUserStats(username) {
  await new Promise((r) => setTimeout(r, 800));
  return {
    username,
    joined: "October 2023",
    last_seen: "2 hours ago",
    global_rank: 14,
    current_streak: 7,
    games_played: 142,
    wins: 95,
    losses: 47,
    win_rate: 66.9,
    games_as_goat: 78,
    wins_as_goat: 56,
    games_as_tiger: 64,
    wins_as_tiger: 39,
    activity: Array.from({ length: 364 }, () =>
      Math.random() > 0.72 ? Math.ceil(Math.random() * 4) : 0,
    ),
  };
}

function initials(u = "") {
  return u.slice(0, 2).toUpperCase();
}
function winPct(wins, played) {
  return played ? Math.round((wins / played) * 100) : 0;
}

// ─── Heatmap intensity levels using goat color ────────────────────────────────
// 0 = empty (bg-darker), 1–4 = increasing opacity on goat green
const HEAT_CLS = [
  "bg-bg-darker",
  "bg-goat opacity-20",
  "bg-goat opacity-40",
  "bg-goat opacity-70",
  "bg-goat",
];
const MONTHS = [
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
  "Jan",
  "Feb",
];
const DAYS = ["", "Mon", "", "Wed", "", "Fri", ""];

// ─── Reusable: Card island ────────────────────────────────────────────────────
function Card({ children, className = "" }) {
  return (
    <div
      className={`bg-bg-surface border border-border-light rounded-xl shadow-lg ${className}`}
    >
      {children}
    </div>
  );
}

// ─── Reusable: Card title ─────────────────────────────────────────────────────
function CardTitle({ children, className = "" }) {
  return (
    <h3 className={`text-text-white font-bold text-lg mb-5 ${className}`}>
      {children}
    </h3>
  );
}

// ─── Reusable: Pill tag ───────────────────────────────────────────────────────
function Tag({ children, accent = false }) {
  return (
    <span
      className={`
        px-3 py-1 rounded-full text-xs font-semibold border whitespace-nowrap
        ${
          accent
            ? "bg-status-info/10 text-status-info border-status-info/20"
            : "bg-bg-dark text-text-muted border-border-light"
        }
      `}
    >
      {children}
    </span>
  );
}

// ─── Reusable: Animated progress bar ─────────────────────────────────────────
function ProgressBar({ pct, colorClass }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 150);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className="h-2.5 bg-bg-dark rounded-full overflow-hidden border border-border-light">
      <div
        className={`h-full rounded-full ${colorClass}`}
        style={{
          width: `${width}%`,
          transition: "width 1.1s cubic-bezier(0.4,0,0.2,1)",
        }}
      />
    </div>
  );
}

// ─── Reusable: Stat tile ──────────────────────────────────────────────────────
function StatTile({ icon, iconBgClass, value, label }) {
  return (
    <Card className="p-6 text-center hover:-translate-y-1 hover:shadow-xl transition-all duration-200 cursor-default">
      <div
        className={`w-10 h-10 rounded-xl ${iconBgClass} mx-auto mb-3 flex items-center justify-center text-lg`}
      >
        {icon}
      </div>
      <div className="text-4xl font-bold text-text-white leading-none">
        {value}
      </div>
      <div className="text-xs text-text-muted mt-1.5 font-semibold uppercase tracking-wider">
        {label}
      </div>
    </Card>
  );
}

// ─── Reusable: Single role row ────────────────────────────────────────────────
function RoleRow({
  role,
  emoji,
  barColorClass,
  dotColorClass,
  textColorClass,
  played,
  wins,
}) {
  const losses = played - wins;
  const pct = winPct(wins, played);
  return (
    <div>
      <div className="flex justify-between items-center mb-2.5">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${dotColorClass} shrink-0`} />
          <span className="text-sm font-semibold text-text-white">
            {emoji} {role}
          </span>
        </div>
        <span className="text-xs text-text-muted">{played} games</span>
        <span className={`text-sm font-bold ${textColorClass}`}>{pct}%</span>
      </div>
      <ProgressBar pct={pct} colorClass={barColorClass} />
      <div className="flex justify-between mt-2 text-xs text-text-muted">
        <span>✓ {wins} wins</span>
        <span>✗ {losses} losses</span>
      </div>
    </div>
  );
}

// ─── Reusable: Donut chart via Chart.js ──────────────────────────────────────
function DonutChart({ wins, losses }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const total = wins + losses;
  const pct = winPct(wins, total);

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();
    chartRef.current = new Chart(canvasRef.current, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [wins, losses],
            // Using your exact CSS var hex values for goat and tiger
            backgroundColor: ["#4ade80", "#f95e5e"],
            borderWidth: 0,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        cutout: "74%",
        plugins: { tooltip: { enabled: true }, legend: { display: false } },
        animation: { animateRotate: true, duration: 1000 },
      },
    });
    return () => chartRef.current?.destroy();
  }, [wins, losses]);

  return (
    <Card className="p-7">
      <CardTitle>Win / Loss Ratio</CardTitle>
      <div className="flex items-center gap-7">
        {/* Donut + center label */}
        <div className="relative w-28 h-28 shrink-0">
          <canvas ref={canvasRef} width={112} height={112} />
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xl font-bold text-text-white leading-none">
              {pct}%
            </span>
            <span className="text-[10px] text-text-muted mt-0.5">win rate</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-3.5 flex-1">
          {[
            { colorClass: "bg-goat", label: "Wins", val: wins },
            { colorClass: "bg-primary", label: "Losses", val: losses },
            {
              colorClass: "bg-bg-dark border border-border-light",
              label: "Total",
              val: total,
            },
          ].map(({ colorClass, label, val }) => (
            <div key={label} className="flex items-center gap-2.5">
              <div
                className={`w-2.5 h-2.5 rounded-full shrink-0 ${colorClass}`}
              />
              <span className="text-sm text-text-muted flex-1">{label}</span>
              <span className="text-sm font-semibold text-text-white">
                {val}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

// ─── Reusable: Role Performance card ─────────────────────────────────────────
function RolesCard({ stats }) {
  return (
    <Card className="p-7">
      <CardTitle>Role Performance</CardTitle>
      <RoleRow
        role="Goat"
        emoji="🐐"
        barColorClass="bg-goat"
        dotColorClass="bg-goat"
        textColorClass="text-goat"
        played={stats.games_as_goat}
        wins={stats.wins_as_goat}
      />
      <div className="h-px bg-border-light my-5" />
      <RoleRow
        role="Tiger"
        emoji="🐅"
        barColorClass="bg-tiger"
        dotColorClass="bg-tiger"
        textColorClass="text-tiger"
        played={stats.games_as_tiger}
        wins={stats.wins_as_tiger}
      />
    </Card>
  );
}

// ─── Reusable: Activity heatmap ───────────────────────────────────────────────
function ActivityHeatmap({ activity, totalGames }) {
  return (
    <Card className="p-7">
      <div className="flex justify-between items-baseline mb-1">
        <CardTitle className="mb-0">Activity</CardTitle>
        <span className="text-xs text-text-muted">
          {totalGames} games · past year
        </span>
      </div>

      {/* Month labels */}
      <div className="flex pl-7 mb-1">
        {MONTHS.map((m) => (
          <div
            key={m}
            className="flex-1 text-[10px] text-text-muted tracking-tight"
          >
            {m}
          </div>
        ))}
      </div>

      <div className="flex gap-1.5">
        {/* Day labels */}
        <div className="flex flex-col gap-[3px] pt-px shrink-0 w-6">
          {DAYS.map((d, i) => (
            <div
              key={i}
              className="h-[11px] text-[9px] text-text-muted leading-[11px]"
            >
              {d}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="overflow-x-auto flex-1">
          <div
            className="grid gap-[3px]"
            style={{
              gridTemplateColumns: "repeat(52, 11px)",
              gridTemplateRows: "repeat(7, 11px)",
              gridAutoFlow: "column",
              width: "max-content",
            }}
          >
            {activity.map((val, i) => (
              <div
                key={i}
                title={`${val} game${val !== 1 ? "s" : ""}`}
                className={`w-[11px] h-[11px] rounded-[3px] ${
                  val === 0
                    ? "bg-bg-darker"
                    : val === 1
                      ? "bg-goat/25"
                      : val === 2
                        ? "bg-goat/50"
                        : val === 3
                          ? "bg-goat/75"
                          : "bg-goat"
                } ${val > 0 ? "cursor-pointer" : ""}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-end gap-1 mt-3 text-[11px] text-text-muted">
        <span>Less</span>
        {[
          "bg-bg-darker border border-border-light",
          "bg-goat/25",
          "bg-goat/50",
          "bg-goat/75",
          "bg-goat",
        ].map((cls, i) => (
          <div key={i} className={`w-[11px] h-[11px] rounded-[3px] ${cls}`} />
        ))}
        <span>More</span>
      </div>
    </Card>
  );
}

// ─── Reusable: Hero / profile header ─────────────────────────────────────────
function HeroCard({ stats }) {
  return (
    <div className="bg-bg-surface border border-border-light rounded-xl shadow-2xl px-10 py-9 flex items-center gap-8 relative overflow-hidden">
      {/* Ambient glow — matches sidebar's primary color */}
      <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-status-info/5 pointer-events-none" />

      {/* Avatar — matches sidebar avatar style */}
      <div className="w-20 h-20 bg-primary rounded-full shrink-0 flex items-center justify-center text-text-white text-3xl font-bold shadow-lg select-none">
        {initials(stats.username)}
      </div>

      {/* Name + meta */}
      <div className="flex-1 min-w-0">
        <h1 className="text-3xl font-bold text-text-white leading-tight">
          {stats.username}
        </h1>
        <p className="text-sm text-text-muted mt-1.5">
          Member since {stats.joined} · Last active {stats.last_seen}
        </p>
        <div className="flex gap-2 mt-3.5 flex-wrap">
          {stats.global_rank <= 20 && <Tag accent>🏆 Top 20 Player</Tag>}
          <Tag>{stats.games_played} games</Tag>
          {stats.current_streak > 0 && (
            <Tag>⚡ {stats.current_streak}-game streak</Tag>
          )}
        </div>
      </div>

      {/* Rank ring */}
      <div className="text-center shrink-0">
        <div className="w-[72px] h-[72px] rounded-full border-[3px] border-primary flex flex-col items-center justify-center mx-auto mb-2 bg-primary/5">
          <span className="text-2xl font-bold text-primary leading-none">
            {stats.global_rank}
          </span>
          <span className="text-[11px] text-text-muted">rank</span>
        </div>
        <span className="text-xs text-text-muted tracking-wide">Global</span>
      </div>
    </div>
  );
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────
function Skeleton({ className = "" }) {
  return (
    <div className={`bg-bg-surface rounded-xl animate-pulse ${className}`} />
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function UserProfilePage({ username = "BaghKali" }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchUserStats(username)
      .then(setStats)
      .catch(() => setError("Could not load profile."))
      .finally(() => setLoading(false));
  }, [username]);

  return (
    <div className="bg-bg-dark min-h-screen py-12 px-5 overflow-y-auto">
      <div className="max-w-300 mx-auto flex flex-col gap-4">
        {/* Loading */}
        {loading && (
          <>
            <Skeleton className="h-36" />
            <div className="grid grid-cols-4 gap-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-52" />
              <Skeleton className="h-52" />
            </div>
            <Skeleton className="h-44" />
          </>
        )}

        {/* Error */}
        {error && (
          <Card className="p-12 text-center">
            <span className="text-status-error text-sm">{error}</span>
          </Card>
        )}

        {/* Loaded */}
        {!loading && !error && stats && (
          <>
            <HeroCard stats={stats} />

            <div className="grid grid-cols-4 gap-3">
              <StatTile
                icon="🎮"
                iconBgClass="bg-status-info/10"
                value={stats.games_played}
                label="Games"
              />
              <StatTile
                icon="✓"
                iconBgClass="bg-goat/10"
                value={stats.wins}
                label="Wins"
              />
              <StatTile
                icon="✗"
                iconBgClass="bg-primary/10"
                value={stats.losses}
                label="Losses"
              />
              <StatTile
                icon="⚡"
                iconBgClass="bg-accent-amber/10"
                value={
                  <>
                    {stats.win_rate}
                    <span className="text-xl font-semibold">%</span>
                  </>
                }
                label="Win Rate"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <DonutChart wins={stats.wins} losses={stats.losses} />
              <RolesCard stats={stats} />
            </div>

            {/* <ActivityHeatmap
              activity={stats.activity}
              totalGames={stats.games_played}
            /> */}
          </>
        )}
      </div>
    </div>
  );
}
