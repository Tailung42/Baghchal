import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Chart, ArcElement, DoughnutController, Tooltip } from "chart.js";
import { userApi } from "../api/client";
import { useUsername } from "../hooks/useUsername";

Chart.register(ArcElement, DoughnutController, Tooltip);

function initials(u = "") {
  return u.slice(0, 2).toUpperCase();
}

function Card({ children, className = "" }) {
  return (
    <div
      className={`bg-bg-surface border border-border-light rounded-xl shadow-lg ${className}`}
    >
      {children}
    </div>
  );
}

function CardTitle({ children }) {
  return <h3 className="text-text-white font-bold text-lg mb-5">{children}</h3>;
}

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

// ── Donut chart ───────────────────────────────────────────────────────────────
function DonutChart({ wins, losses }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const total = wins + losses;
  const pct = total ? Math.round((wins / total) * 100) : 0;

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();
    chartRef.current = new Chart(canvasRef.current, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [wins, losses],
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
        <div className="relative w-28 h-28 shrink-0">
          <canvas ref={canvasRef} width={112} height={112} />
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xl font-bold text-text-white leading-none">
              {pct}%
            </span>
            <span className="text-[10px] text-text-muted mt-0.5">win rate</span>
          </div>
        </div>
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

function RolesCard({ stats }) {
  const roles = [
    {
      label: "Goat",
      emoji: "🐐",
      barColor: "bg-goat",
      dotColor: "bg-goat",
      textColor: "text-goat",
      played: stats.games_as_goat,
      wins: stats.wins_as_goat,
    },
    {
      label: "Tiger",
      emoji: "🐅",
      barColor: "bg-tiger",
      dotColor: "bg-tiger",
      textColor: "text-tiger",
      played: stats.games_as_tiger,
      wins: stats.wins_as_tiger,
    },
  ];

  return (
    <Card className="p-7">
      <CardTitle>Role Performance</CardTitle>
      <div className="space-y-6">
        {roles.map(
          (
            { label, emoji, barColor, dotColor, textColor, played, wins },
            i,
          ) => {
            const losses = played - wins;
            const pct = played ? Math.round((wins / played) * 100) : 0;
            return (
              <div key={label}>
                {i > 0 && <div className="h-px bg-border-light mb-6" />}
                <div className="flex justify-between items-center mb-2.5">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${dotColor}`} />
                    <span className="text-sm font-semibold text-text-white">
                      {emoji} {label}
                    </span>
                  </div>
                  <span className="text-xs text-text-muted">
                    {played} games
                  </span>
                  <span className={`text-sm font-bold ${textColor}`}>
                    {pct}%
                  </span>
                </div>
                <ProgressBar pct={pct} colorClass={barColor} />
                <div className="flex justify-between mt-2 text-xs text-text-muted">
                  <span>✓ {wins} wins</span>
                  <span>✗ {losses} losses</span>
                </div>
              </div>
            );
          },
        )}
      </div>
    </Card>
  );
}

function Skeleton({ className = "" }) {
  return (
    <div className={`bg-bg-surface rounded-xl animate-pulse ${className}`} />
  );
}

export default function UserProfile() {
  const { username } = useParams();
  const { username: currentUser } = useUsername();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // fetch userstats on mount
  useEffect(() => {
    if (!username) return;
    setLoading(true);
    setError(null);
    userApi
      .getProfile(username)
      .then((res) => {
        // backend returns an array with a JSON string as first element
        const raw = res.data;
        const parsed = Array.isArray(raw) ? JSON.parse(raw[0]) : raw;
        setStats({ username, ...parsed });
      })
      .catch(() => setError("Could not load profile."))
      .finally(() => setLoading(false));
  }, []);

  const isOwnProfile = username === currentUser;

  return (
    <div className="bg-bg-dark min-h-screen py-10 px-5 overflow-y-auto">
      <div className="max-w-300 mx-auto flex flex-col gap-4">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="self-start text-sm text-text-muted hover:text-text-light transition-colors"
        >
          ← Back
        </button>

        {/* Loading */}
        {loading && (
          <>
            <Skeleton className="h-32" />
            <div className="grid grid-cols-4 gap-3">
              <Skeleton className="h-28" />
              <Skeleton className="h-28" />
              <Skeleton className="h-28" />
              <Skeleton className="h-28" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-52" />
              <Skeleton className="h-52" />
            </div>
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
            {/* Hero */}
            <Card className="px-8 py-7 flex items-center gap-6">
              <div className="w-16 h-16 bg-primary rounded-full shrink-0 flex items-center justify-center text-text-white text-2xl font-bold shadow-lg select-none">
                {initials(stats.username)}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-text-white">
                  {stats.username}
                </h1>
                {isOwnProfile && (
                  <p className="text-xs text-text-muted mt-1">Your profile</p>
                )}
              </div>
            </Card>

            {/* Stat tiles */}
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

            {/* Charts */}
            <div className="grid grid-cols-2 gap-4">
              <DonutChart wins={stats.wins} losses={stats.losses} />
              <RolesCard stats={stats} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
