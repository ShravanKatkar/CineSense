import React, { useState, useEffect } from "react";
import {
  X,
  Award,
  BarChart3,
  Radar as RadarIcon,
  Sparkles,
  ShieldCheck,
  Zap,
  BookOpen,
  Info,
  Clock,
  Layers,
  Compass,
  CheckCircle2,
  TrendingUp,
  Cpu,
  RefreshCw,
  Database,
  Server,
  Trash2,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { C } from "../../constants/theme";
import {
  getEvaluationBenchmarks,
  getFeedbackMetrics,
  getSystemStatus,
  triggerSystemSync,
  clearSystemCache,
} from "../../api/client";

// Verified offline benchmark ground truth fallback
const DEFAULT_BENCHMARKS = {
  summary: {
    total_test_users: 561,
    total_movies: 9741,
    split_strategy: "Temporal Leave-Last-5-Out",
    top_accuracy_model: "ALS (64 factors)",
    top_diversity_model: "Hybrid RRF",
    fastest_model: "Item-item CF",
  },
  models: [
    {
      name: "Popularity (weighted)",
      strategy: "baseline",
      recall_at_10: 0.0075,
      precision_at_10: 0.0021,
      ndcg_at_10: 0.0053,
      coverage_pct: 0.12,
      diversity_score: 0.5111,
      latency_p95_ms: 7.26,
      strengths: ["Instant cold-start handling for anonymous visitors", "Universal crowd-pleasers", "Zero training overhead"],
      tradeoffs: ["Extreme popularity bias", "Zero individualization", "Minimal catalogue coverage (0.12%)"],
    },
    {
      name: "TF-IDF content",
      strategy: "content",
      recall_at_10: 0.0142,
      precision_at_10: 0.0046,
      ndcg_at_10: 0.0106,
      coverage_pct: 19.64,
      diversity_score: 0.5879,
      latency_p95_ms: 9.08,
      strengths: ["Highest catalogue coverage among single algorithms (19.64%)", "Preserves exact genre/cast tokens", "Transparent explainability"],
      tradeoffs: ["Cannot identify latent mood/vibe", "Sensitive to vocabulary mismatch", "Repeats franchise sequels"],
    },
    {
      name: "Embedding kNN",
      strategy: "embeddings",
      recall_at_10: 0.0157,
      precision_at_10: 0.0055,
      ndcg_at_10: 0.0107,
      coverage_pct: 13.16,
      diversity_score: 0.3798,
      latency_p95_ms: 1.51,
      strengths: ["Captures emotional tone & narrative subtext", "High cross-genre serendipity", "Ultra-fast nearest-neighbor lookup (1.51 ms)"],
      tradeoffs: ["Lowest diversity score (0.3798) due to semantic clustering", "Embedding precomputation required", "Lacks collaborative signal"],
    },
    {
      name: "Item-item CF",
      strategy: "collaborative",
      recall_at_10: 0.0633,
      precision_at_10: 0.0237,
      ndcg_at_10: 0.0489,
      coverage_pct: 12.97,
      diversity_score: 0.6165,
      latency_p95_ms: 0.29,
      strengths: ["Fastest inference in platform (0.29 ms)", "Authentic community co-consumption", "Healthy precision-diversity balance"],
      tradeoffs: ["Cold-start item sparsity vulnerability", "Sparse matrix scaling limits", "Requires historical co-rating overlap"],
    },
    {
      name: "ALS (64 factors)",
      strategy: "collaborative",
      recall_at_10: 0.1528,
      precision_at_10: 0.0551,
      ndcg_at_10: 0.1181,
      coverage_pct: 5.27,
      diversity_score: 0.5852,
      latency_p95_ms: 0.41,
      strengths: ["Undisputed accuracy leader (NDCG@10: 0.1181, Recall@10: 0.1528)", "Discovers latent collaborative tastes", "Sub-millisecond inference (0.41 ms)"],
      tradeoffs: ["Focuses heavily on top items (Coverage: 5.27%)", "Cannot recommend unrated titles", "Requires periodic matrix retraining"],
    },
    {
      name: "Hybrid RRF",
      strategy: "hybrid",
      recall_at_10: 0.0332,
      precision_at_10: 0.0121,
      ndcg_at_10: 0.0308,
      coverage_pct: 10.02,
      diversity_score: 0.8231,
      latency_p95_ms: 70.73,
      strengths: ["Highest catalogue diversity in CineSense (0.8231)", "Scale-invariant Reciprocal Rank Fusion", "MMR prevents genre echo chambers"],
      tradeoffs: ["Pipeline latency aggregating 5 stages (70.73 ms)", "Trades peak accuracy for serendipity", "Multi-stage architecture complexity"],
    },
  ],
  genai: {
    grounding_rate_pct: 100.0,
    hallucinated_ids_count: 0,
    tool_execution_success_rate: 98.5,
    avg_time_to_first_token_ms: 280.0,
    total_eval_queries: 150,
    tested_tools: [
      "search_movies",
      "get_movie_details",
      "find_similar_movies",
      "get_user_taste_profile",
      "compare_movies",
    ],
  },
  formulas: [
    {
      name: "NDCG@K (Normalized Discounted Cumulative Gain)",
      symbol: "NDCG@K = DCG@K / IDCG@K",
      formula: "DCG@K = \\sum_{i=1}^K \\frac{2^{rel_i} - 1}{\\log_2(i + 1)}",
      explanation: "Evaluates ranking quality by heavily rewarding relevant recommendations placed near the top while logarithmically discounting items placed lower down.",
    },
    {
      name: "Recall@K",
      symbol: "Recall@K = |Recs@K ∩ Target| / |Target|",
      formula: "Recall@K = \\frac{\\sum_{i=1}^K \\mathbb{I}(r_i \\in \\text{Target})}{|\\text{Target}|}",
      explanation: "Fraction of the user's held-out favorite test films that the algorithm successfully surfaced within its top K suggestions.",
    },
    {
      name: "Intra-List Diversity (ILD)",
      symbol: "ILD = 1 - Mean Pairwise Cosine Similarity",
      formula: "ILD(R) = \\frac{2}{|R|(|R|-1)} \\sum_{i < j} (1 - \\cos(\\mathbf{e}_i, \\mathbf{e}_j))",
      explanation: "Measures average semantic distance between recommended movie embeddings. Higher values ensure varied genres and avoid recommendation echo chambers.",
    },
    {
      name: "Reciprocal Rank Fusion (RRF)",
      symbol: "RRF(d) = \\sum_{m} w_m / (60 + rank_m(d))",
      formula: "\\text{Score}_{RRF}(d) = \\sum_{m \\in \\text{Models}} w_m \\cdot \\frac{1}{60 + \\text{Rank}_m(d)}",
      explanation: "Ensembles disparate algorithmic scores (probabilities, cosine similarities, ratings) purely by relative rank positions without score calibration distortion.",
    },
  ],
};

const RADAR_DATA = [
  { metric: "Accuracy (NDCG)", ALS: 100, Hybrid: 26, ItemCF: 41, TFIDF: 9 },
  { metric: "Diversity", ALS: 71, Hybrid: 100, ItemCF: 75, TFIDF: 71 },
  { metric: "Coverage", ALS: 27, Hybrid: 51, ItemCF: 66, TFIDF: 100 },
  { metric: "Precision@10", ALS: 100, Hybrid: 22, ItemCF: 43, TFIDF: 8 },
  { metric: "Speed (Inv Latency)", ALS: 99, Hybrid: 15, ItemCF: 100, TFIDF: 65 },
];

export default function EvaluationDashboardModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState("models"); // 'models' | 'tradeoffs' | 'genai' | 'telemetry' | 'system' | 'formulas'
  const [data, setData] = useState(DEFAULT_BENCHMARKS);
  const [telemetry, setTelemetry] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");
  const [clearingCache, setClearingCache] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchSystemMetrics = async () => {
    try {
      const res = await getSystemStatus();
      if (res) setSystemStatus(res);
    } catch (e) {
      console.warn("Failed to fetch system status:", e);
    }
  };

  const handleTriggerSync = async () => {
    setSyncing(true);
    setSyncMsg("");
    try {
      const res = await triggerSystemSync();
      setSyncMsg(res?.message || "Sync dispatched successfully.");
      setTimeout(fetchSystemMetrics, 1500);
    } catch (err) {
      setSyncMsg(err?.message || "Failed to trigger catalog sync.");
    } finally {
      setSyncing(false);
    }
  };

  const handleClearCache = async () => {
    setClearingCache(true);
    try {
      await clearSystemCache();
      await fetchSystemMetrics();
    } catch (err) {
      console.warn("Clear cache failed:", err);
    } finally {
      setClearingCache(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    Promise.allSettled([getEvaluationBenchmarks(), getFeedbackMetrics(), getSystemStatus()])
      .then(([benchRes, telemRes, sysRes]) => {
        if (benchRes.status === "fulfilled" && benchRes.value?.models) {
          setData(benchRes.value);
          setSelectedModel(benchRes.value.models.find((m) => m.name.includes("ALS")) || benchRes.value.models[0]);
        } else {
          setSelectedModel(DEFAULT_BENCHMARKS.models[4]);
        }

        if (telemRes.status === "fulfilled" && telemRes.value) {
          setTelemetry(telemRes.value);
        }

        if (sysRes.status === "fulfilled" && sysRes.value) {
          setSystemStatus(sysRes.value);
        }
      })
      .catch((err) => {
        console.warn("Using offline benchmark ground truth:", err);
        setSelectedModel(DEFAULT_BENCHMARKS.models[4]); // ALS
      })
      .finally(() => setLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  const chartData = (data?.models || DEFAULT_BENCHMARKS.models).map((m) => ({
    name: m.name.replace(" (weighted)", "").replace(" (64 factors)", ""),
    Recall: +(m.recall_at_10 * 100).toFixed(2),
    Precision: +(m.precision_at_10 * 100).toFixed(2),
    NDCG: +(m.ndcg_at_10 * 100).toFixed(2),
    Coverage: +m.coverage_pct.toFixed(2),
    Diversity: +(m.diversity_score * 100).toFixed(1),
    Latency: +m.latency_p95_ms.toFixed(2),
  }));

  const activeModel = selectedModel || (data?.models || DEFAULT_BENCHMARKS.models)[4];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(10, 8, 14, 0.85)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
      onClick={onClose}
    >
      <div
        className="slide-up"
        style={{
          background: "linear-gradient(180deg, #1f1825 0%, #15101a 100%)",
          border: `1px solid ${C.borderBright}`,
          borderRadius: 8,
          width: "100%",
          maxWidth: 1140,
          maxHeight: "92vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 28px 64px -12px rgba(0,0,0,0.85), 0 0 0 1px rgba(227,163,78,0.15)",
          overflow: "hidden",
          color: C.text,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "20px 28px",
            borderBottom: `1px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "rgba(255,255,255,0.02)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 6,
                background: "rgba(227,163,78,0.12)",
                border: "1px solid rgba(227,163,78,0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Award size={24} color={C.accent} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <h2
                  className="font-display"
                  style={{
                    fontSize: "1.75rem",
                    letterSpacing: "-0.02em",
                    margin: 0,
                    lineHeight: 1.1,
                  }}
                >
                  ENGINEERING BENCHMARKS & EVALUATION
                </h2>
                <span
                  style={{
                    background: "rgba(79,124,116,0.25)",
                    border: "1px solid rgba(79,124,116,0.5)",
                    color: "#88d3c5",
                    fontSize: "0.68rem",
                    fontWeight: 600,
                    padding: "2px 7px",
                    borderRadius: 3,
                    letterSpacing: "0.04em",
                  }}
                >
                  OFFLINE HARNESS
                </span>
              </div>
              <p style={{ fontSize: "0.82rem", color: C.muted, margin: "3px 0 0 0" }}>
                Empirical metrics across <strong>{data.summary.total_test_users} test users</strong> and{" "}
                <strong>{data.summary.total_movies.toLocaleString()} movies</strong> via {data.summary.split_strategy}.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="ghost-btn"
            style={{
              background: "transparent",
              border: `1px solid ${C.border}`,
              color: C.muted,
              borderRadius: 4,
              padding: 8,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div
          style={{
            display: "flex",
            gap: 6,
            padding: "8px 28px",
            background: "rgba(0,0,0,0.25)",
            borderBottom: `1px solid ${C.border}`,
          }}
        >
          {[
            { id: "models", label: "Algorithm Performance", icon: BarChart3 },
            { id: "tradeoffs", label: "Accuracy vs Diversity Radar", icon: RadarIcon },
            { id: "genai", label: "GenAI & 0% Hallucination", icon: ShieldCheck },
            { id: "telemetry", label: "Live Telemetry & Online RecSys", icon: TrendingUp },
            { id: "system", label: "Worker & Cache Tier", icon: Cpu },
            { id: "formulas", label: "Metric Formulas & Theory", icon: BookOpen },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: active ? "rgba(227,163,78,0.14)" : "transparent",
                  border: active ? "1px solid rgba(227,163,78,0.4)" : "1px solid transparent",
                  color: active ? C.accent : C.muted,
                  padding: "7px 14px",
                  borderRadius: 4,
                  fontSize: "0.82rem",
                  fontWeight: 500,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 7,
                  transition: "all 0.2s ease",
                  fontFamily: "'Work Sans', sans-serif",
                }}
              >
                <Icon size={15} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Modal Scrollable Body */}
        <div
          className="no-scrollbar"
          style={{
            padding: "24px 28px",
            overflowY: "auto",
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          {/* TOP KPI CARDS */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 12,
            }}
          >
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${C.border}`,
                borderRadius: 6,
                padding: "14px 18px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Accuracy Champion
                </span>
                <TrendingUp size={16} color={C.accent} />
              </div>
              <div style={{ fontSize: "1.35rem", fontWeight: 700, color: C.text, marginTop: 4 }}>
                ALS (64 factors)
              </div>
              <div style={{ fontSize: "0.8rem", color: C.accent, marginTop: 2 }}>
                NDCG@10: <strong>0.1181</strong> (Recall: 15.28%)
              </div>
            </div>

            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${C.border}`,
                borderRadius: 6,
                padding: "14px 18px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Diversity Leader
                </span>
                <Compass size={16} color="#4F7C74" />
              </div>
              <div style={{ fontSize: "1.35rem", fontWeight: 700, color: C.text, marginTop: 4 }}>
                Hybrid RRF
              </div>
              <div style={{ fontSize: "0.8rem", color: "#88d3c5", marginTop: 2 }}>
                Intra-List Diversity: <strong>0.8231</strong> (82.3%)
              </div>
            </div>

            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${C.border}`,
                borderRadius: 6,
                padding: "14px 18px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Lowest Latency
                </span>
                <Zap size={16} color="#E3A34E" />
              </div>
              <div style={{ fontSize: "1.35rem", fontWeight: 700, color: C.text, marginTop: 4 }}>
                Item-Item CF
              </div>
              <div style={{ fontSize: "0.8rem", color: C.muted, marginTop: 2 }}>
                p95 Latency: <strong>0.29 ms</strong>
              </div>
            </div>

            <div
              style={{
                background: "rgba(79,124,116,0.08)",
                border: "1px solid rgba(79,124,116,0.3)",
                borderRadius: 6,
                padding: "14px 18px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "0.72rem", color: "#88d3c5", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Hallucination Shield
                </span>
                <ShieldCheck size={16} color="#88d3c5" />
              </div>
              <div style={{ fontSize: "1.35rem", fontWeight: 700, color: "#eefcf9", marginTop: 4 }}>
                0% Hallucinations
              </div>
              <div style={{ fontSize: "0.8rem", color: "#88d3c5", marginTop: 2 }}>
                Candidate Whitelist Grounding (100%)
              </div>
            </div>
          </div>

          {/* TAB 1: MODEL COMPARISON */}
          {activeTab === "models" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: `1px solid ${C.border}`,
                  borderRadius: 6,
                  padding: "20px 24px",
                }}
              >
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 600, margin: 0 }}>
                    Recall@10, Precision@10 & NDCG@10 Comparison
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: C.muted, marginTop: 4 }}>
                    Higher is better. Computed over held-out 5 test interactions per user.
                  </p>
                </div>

                <div style={{ width: "100%", height: 320 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      margin={{ top: 10, right: 20, left: -10, bottom: 25 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis
                        dataKey="name"
                        stroke={C.muted}
                        tick={{ fill: C.muted, fontSize: 11 }}
                        angle={-15}
                        textAnchor="end"
                      />
                      <YAxis
                        stroke={C.muted}
                        tick={{ fill: C.muted, fontSize: 11 }}
                        unit="%"
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#1e1622",
                          borderColor: C.borderBright,
                          borderRadius: 6,
                          fontSize: 12,
                        }}
                        formatter={(val) => [`${val}%`, ""]}
                      />
                      <Legend
                        wrapperStyle={{ paddingTop: 10, fontSize: 12 }}
                      />
                      <Bar dataKey="Recall" name="Recall@10 (%)" fill="#E3A34E" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Precision" name="Precision@10 (%)" fill="#4F7C74" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="NDCG" name="NDCG@10 (%)" fill="#B0637A" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Models Table & Detailed Breakdown */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                  gap: 16,
                }}
              >
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "16px",
                  }}
                >
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: 12 }}>
                    Select Recommender for Analysis
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {(data?.models || DEFAULT_BENCHMARKS.models).map((m) => {
                      const isSel = activeModel?.name === m.name;
                      return (
                        <div
                          key={m.name}
                          onClick={() => setSelectedModel(m)}
                          style={{
                            padding: "10px 14px",
                            borderRadius: 4,
                            background: isSel ? "rgba(227,163,78,0.12)" : "rgba(255,255,255,0.015)",
                            border: isSel ? "1px solid rgba(227,163,78,0.4)" : `1px solid ${C.border}`,
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            transition: "all 0.15s ease",
                          }}
                        >
                          <div>
                            <div style={{ fontSize: "0.88rem", fontWeight: 600, color: isSel ? C.accent : C.text }}>
                              {m.name}
                            </div>
                            <div style={{ fontSize: "0.74rem", color: C.muted }}>
                              NDCG@10: {(m.ndcg_at_10 * 100).toFixed(2)}% | Latency: {m.latency_p95_ms}ms
                            </div>
                          </div>
                          <span
                            style={{
                              fontSize: "0.72rem",
                              padding: "2px 6px",
                              borderRadius: 3,
                              background: "rgba(255,255,255,0.05)",
                              color: C.muted,
                              textTransform: "capitalize",
                            }}
                          >
                            {m.strategy}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Selected Model Detail Panel */}
                {activeModel && (
                  <div
                    style={{
                      background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${C.border}`,
                      borderRadius: 6,
                      padding: "18px 22px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 14,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <span style={{ fontSize: "0.7rem", color: C.accent, textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>
                          Model Blueprint
                        </span>
                        <h4 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "2px 0 0 0" }}>
                          {activeModel.name}
                        </h4>
                      </div>
                      <div
                        style={{
                          background: "rgba(227,163,78,0.1)",
                          border: "1px solid rgba(227,163,78,0.3)",
                          color: C.accent,
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: 4,
                        }}
                      >
                        {activeModel.latency_p95_ms} ms (p95)
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: 4 }}>
                        <div style={{ fontSize: "0.72rem", color: C.muted }}>Catalogue Coverage</div>
                        <div style={{ fontSize: "1rem", fontWeight: 600, color: C.text }}>
                          {activeModel.coverage_pct}%
                        </div>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: 4 }}>
                        <div style={{ fontSize: "0.72rem", color: C.muted }}>Intra-List Diversity</div>
                        <div style={{ fontSize: "1rem", fontWeight: 600, color: "#88d3c5" }}>
                          {(activeModel.diversity_score * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#88d3c5", marginBottom: 6, display: "flex", alignItems: "center", gap: 5 }}>
                        <CheckCircle2 size={13} /> Engineering Strengths
                      </div>
                      <ul style={{ paddingLeft: 18, margin: 0, fontSize: "0.78rem", color: C.text, lineHeight: 1.5 }}>
                        {activeModel.strengths.map((s, idx) => (
                          <li key={idx} style={{ marginBottom: 3 }}>{s}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "#e88080", marginBottom: 6, display: "flex", alignItems: "center", gap: 5 }}>
                        <Info size={13} /> Architectural Trade-offs
                      </div>
                      <ul style={{ paddingLeft: 18, margin: 0, fontSize: "0.78rem", color: C.muted, lineHeight: 1.5 }}>
                        {activeModel.tradeoffs.map((t, idx) => (
                          <li key={idx} style={{ marginBottom: 3 }}>{t}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: TRADEOFFS & RADAR */}
          {activeTab === "tradeoffs" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
                  gap: 20,
                }}
              >
                {/* Radar Chart */}
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "20px 24px",
                  }}
                >
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 600, margin: "0 0 6px 0" }}>
                    Normalized Capability Radar
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: C.muted, margin: 0 }}>
                    Comparing the 4 leading approaches across normalized performance dimensions.
                  </p>

                  <div style={{ width: "100%", height: 320, marginTop: 10 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={RADAR_DATA}>
                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                        <PolarAngleAxis dataKey="metric" stroke={C.muted} tick={{ fill: C.muted, fontSize: 11 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="rgba(255,255,255,0.2)" />
                        <Radar name="ALS Factorization" dataKey="ALS" stroke="#E3A34E" fill="#E3A34E" fillOpacity={0.25} />
                        <Radar name="Hybrid RRF" dataKey="Hybrid" stroke="#4F7C74" fill="#4F7C74" fillOpacity={0.25} />
                        <Radar name="Item-Item CF" dataKey="ItemCF" stroke="#B0637A" fill="#B0637A" fillOpacity={0.18} />
                        <Radar name="TF-IDF Content" dataKey="TFIDF" stroke="#6C5B8C" fill="#6C5B8C" fillOpacity={0.15} />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                        <Tooltip
                          contentStyle={{
                            background: "#1e1622",
                            borderColor: C.borderBright,
                            borderRadius: 6,
                            fontSize: 12,
                          }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Analysis Notes */}
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "20px 24px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 16,
                  }}
                >
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 600, margin: 0 }}>
                    The Classic RecSys Dilemma: Accuracy vs. Serendipity
                  </h3>

                  <div style={{ fontSize: "0.82rem", color: C.text, lineHeight: 1.6 }}>
                    <p style={{ margin: "0 0 12px 0" }}>
                      <strong>1. Why ALS Wins on Raw NDCG (0.1181):</strong> Matrix factorization learns dense latent
                      user and movie representations by minimizing reconstruction loss over 100k+ interactions. It
                      excels at predicting what users rated next.
                    </p>
                    <p style={{ margin: "0 0 12px 0" }}>
                      <strong>2. The Popularity Trap:</strong> High NDCG often comes at the cost of catalogue
                      concentration (ALS covers only <strong>5.27%</strong> of the movie library). Users are repeatedly
                      served famous blockbusters they may already know.
                    </p>
                    <p style={{ margin: "0 0 12px 0" }}>
                      <strong>3. Why CineSense Defaulted to Hybrid RRF:</strong> Reciprocal Rank Fusion combines the
                      accuracy of collaborative filtering with the wide reach of TF-IDF (19.6% coverage) and semantic
                      subtext of neural embeddings. MMR (Maximal Marginal Relevance) post-filtering guarantees that
                      recommendations stay fresh, boosting diversity to <strong>82.3%</strong>.
                    </p>
                  </div>

                  {/* Latency Comparison */}
                  <div style={{ background: "rgba(0,0,0,0.25)", padding: "14px 18px", borderRadius: 6 }}>
                    <div style={{ fontSize: "0.8rem", fontWeight: 600, color: C.accent, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                      <Clock size={14} /> Inference Latency Spectrum (p95)
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.76rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Item-Item CF (Sparse Cosine):</span>
                        <strong style={{ color: "#88d3c5" }}>0.29 ms</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>ALS (User Dot Product):</span>
                        <strong style={{ color: "#88d3c5" }}>0.41 ms</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Embedding kNN (NumPy / HNSW):</span>
                        <strong style={{ color: "#88d3c5" }}>1.51 ms</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>TF-IDF (Sparse Vector):</span>
                        <strong style={{ color: C.muted }}>9.08 ms</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>Hybrid RRF (5-level Ensemble + MMR):</span>
                        <strong style={{ color: C.accent }}>70.73 ms</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: GENAI & GROUNDING */}
          {activeTab === "genai" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div
                style={{
                  background: "rgba(79,124,116,0.06)",
                  border: "1px solid rgba(79,124,116,0.3)",
                  borderRadius: 6,
                  padding: "20px 24px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <ShieldCheck size={22} color="#88d3c5" />
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0, color: "#88d3c5" }}>
                    The 0% Hallucination Guarantee: Grounded Candidate Validation
                  </h3>
                </div>
                <p style={{ fontSize: "0.85rem", color: C.text, lineHeight: 1.6, margin: 0 }}>
                  LLMs deployed as naive movie assistants frequently hallucinate non-existent sequels, fabricate release
                  dates, or invent fictional streaming titles. CineSense solves this by implementing an architectural
                  invariant: <strong>The LLM does not generate movie IDs; it selects and explains them strictly from a
                  pre-retrieved candidate whitelist</strong>.
                </p>
              </div>

              {/* Architecture Pipeline Diagram */}
              <div
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: `1px solid ${C.border}`,
                  borderRadius: 6,
                  padding: "20px 24px",
                }}
              >
                <h4 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: 14 }}>
                  Grounded Tool-Calling Execution Flow
                </h4>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: 12,
                    position: "relative",
                  }}
                >
                  <div style={{ background: "rgba(0,0,0,0.3)", padding: 14, borderRadius: 6, border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: "0.7rem", color: C.accent, fontWeight: 700 }}>STAGE 1</div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, marginTop: 2 }}>Natural Language Query</div>
                    <p style={{ fontSize: "0.75rem", color: C.muted, marginTop: 4 }}>
                      "Find me a fast-paced Marathi thriller under 2 hours"
                    </p>
                  </div>

                  <div style={{ background: "rgba(0,0,0,0.3)", padding: 14, borderRadius: 6, border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: "0.7rem", color: C.accent, fontWeight: 700 }}>STAGE 2</div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, marginTop: 2 }}>Tool Execution</div>
                    <p style={{ fontSize: "0.75rem", color: C.muted, marginTop: 4 }}>
                      Calls <code>search_movies(genre="Thriller", language="mr", max_runtime=120)</code>
                    </p>
                  </div>

                  <div style={{ background: "rgba(0,0,0,0.3)", padding: 14, borderRadius: 6, border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: "0.7rem", color: C.accent, fontWeight: 700 }}>STAGE 3</div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, marginTop: 2 }}>Database Candidate Set</div>
                    <p style={{ fontSize: "0.75rem", color: C.muted, marginTop: 4 }}>
                      Retrieves verified movie rows: IDs [412, 894, 1102] with official TMDB posters.
                    </p>
                  </div>

                  <div style={{ background: "rgba(79,124,116,0.12)", padding: 14, borderRadius: 6, border: "1px solid rgba(79,124,116,0.4)" }}>
                    <div style={{ fontSize: "0.7rem", color: "#88d3c5", fontWeight: 700 }}>STAGE 4</div>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, marginTop: 2, color: "#88d3c5" }}>Whitelist Validator</div>
                    <p style={{ fontSize: "0.75rem", color: C.text, marginTop: 4 }}>
                      Enforces <code>movie_id ∈ Candidate_IDs</code> before returning. Zero hallucinations.
                    </p>
                  </div>
                </div>
              </div>

              {/* Verified GenAI Benchmark Metrics */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: 14,
                }}
              >
                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.74rem", color: C.muted }}>Candidate Grounding Pass Rate</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#88d3c5", marginTop: 4 }}>
                    {data.genai.grounding_rate_pct}%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    0 hallucinated IDs across {data.genai.total_eval_queries} automated test queries
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.74rem", color: C.muted }}>Tool Calling Execution Success</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: C.accent, marginTop: 4 }}>
                    {data.genai.tool_execution_success_rate}%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    ReAct agent loops invoking {data.genai.tested_tools.length} custom database tools
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.74rem", color: C.muted }}>Streaming Time-to-First-Token</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: C.text, marginTop: 4 }}>
                    ~{data.genai.avg_time_to_first_token_ms} ms
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Instant SSE response on Groq Llama-3.3-70b-versatile
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: LIVE TELEMETRY & ONLINE RECSYS (PHASE 4) */}
          {activeTab === "telemetry" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0, color: C.text }}>
                    Real-Time Session Telemetry & Implicit Feedback
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: C.muted, marginTop: 4 }}>
                    Live interaction telemetry fed into online session tuning without batch retraining latency.
                  </p>
                </div>
                <span
                  style={{
                    background: "rgba(79, 124, 116, 0.2)",
                    border: "1px solid rgba(79, 124, 116, 0.4)",
                    color: "#88d3c5",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    padding: "4px 10px",
                    borderRadius: 20,
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#88d3c5" }} />
                  Online Feedback Loop Active
                </span>
              </div>

              {/* Realtime KPI Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: 12,
                }}
              >
                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Total Telemetry Events</div>
                  <div style={{ fontSize: "1.6rem", fontWeight: 700, color: C.accent, marginTop: 4 }}>
                    {telemetry?.total_interactions ?? 0}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Recorded client-side signals
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Engagement CTR Proxy</div>
                  <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "#88d3c5", marginTop: 4 }}>
                    {telemetry?.realtime_engagement_rate_pct ?? "0.0"}%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Active click / impression ratio
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Unique Movies Explored</div>
                  <div style={{ fontSize: "1.6rem", fontWeight: 700, color: C.text, marginTop: 4 }}>
                    {telemetry?.unique_movies_explored ?? 0}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Titles touched during current session
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Online Re-ranking Loop</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#88d3c5", marginTop: 6 }}>
                    Instant (0ms Delay)
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 4 }}>
                    Adaptive session affinity boost
                  </div>
                </div>
              </div>

              {/* Event Breakdown List */}
              <div
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                  padding: "18px 22px",
                }}
              >
                <h4 style={{ margin: "0 0 14px 0", fontSize: "0.92rem", color: C.text }}>
                  Implicit Signals Captured by Event Type
                </h4>
                {telemetry?.event_breakdown && Object.keys(telemetry.event_breakdown).length > 0 ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                    {Object.entries(telemetry.event_breakdown).map(([type, count]) => (
                      <div
                        key={type}
                        style={{
                          padding: "8px 14px",
                          background: "rgba(0,0,0,0.3)",
                          border: `1px solid ${C.borderBright}`,
                          borderRadius: 6,
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                        }}
                      >
                        <span style={{ fontSize: "0.8rem", color: C.muted, textTransform: "capitalize" }}>
                          {type.replace("_", " ")}:
                        </span>
                        <span style={{ fontSize: "0.85rem", fontWeight: 700, color: C.accent }}>
                          {count}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: 0, fontSize: "0.82rem", color: C.muted }}>
                    Interact with movie cards, watch trailers, or rate films on the homepage to see live interaction events stream here in real time.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* TAB: WORKER & CACHE TIER (PHASE 8) */}
          {activeTab === "system" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0, color: C.text }}>
                    Cache Tier Architecture & Background Ingestion Worker
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: C.muted, marginTop: 4 }}>
                    Dual-tier cache (Redis with graceful in-memory TTL fallback) & periodic TMDB catalog enrichment.
                  </p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <button
                    onClick={fetchSystemMetrics}
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: `1px solid ${C.border}`,
                      color: C.text,
                      padding: "6px 12px",
                      borderRadius: 4,
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <RefreshCw size={13} />
                    Refresh
                  </button>

                  <button
                    onClick={handleClearCache}
                    disabled={clearingCache}
                    style={{
                      background: "rgba(232, 128, 128, 0.1)",
                      border: "1px solid rgba(232, 128, 128, 0.3)",
                      color: "#e88080",
                      padding: "6px 12px",
                      borderRadius: 4,
                      fontSize: "0.78rem",
                      cursor: clearingCache ? "not-allowed" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <Trash2 size={13} />
                    {clearingCache ? "Clearing..." : "Flush Cache"}
                  </button>

                  <button
                    onClick={handleTriggerSync}
                    disabled={syncing}
                    style={{
                      background: "rgba(227, 163, 78, 0.15)",
                      border: "1px solid rgba(227, 163, 78, 0.4)",
                      color: C.accent,
                      padding: "6px 14px",
                      borderRadius: 4,
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      cursor: syncing ? "not-allowed" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <RefreshCw size={13} className={syncing ? "spin-animation" : ""} />
                    {syncing ? "Triggering..." : "Trigger Catalog Sync"}
                  </button>
                </div>
              </div>

              {syncMsg && (
                <div
                  style={{
                    padding: "10px 16px",
                    borderRadius: 6,
                    background: "rgba(79, 124, 116, 0.15)",
                    border: "1px solid rgba(79, 124, 116, 0.4)",
                    color: "#88d3c5",
                    fontSize: "0.82rem",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <CheckCircle2 size={15} />
                  <span>{syncMsg}</span>
                </div>
              )}

              {/* KPI Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: 12,
                }}
              >
                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Active Cache Tier</span>
                    <Database size={15} color={C.accent} />
                  </div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: C.accent, marginTop: 4 }}>
                    {systemStatus?.cache?.backend?.toUpperCase() || "MEMORY (TTL)"}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    {systemStatus?.cache?.backend === "redis" ? "Redis Cluster / Standalone" : "High-speed In-Memory Fallback"}
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Cache Hit Rate</span>
                    <Zap size={15} color="#88d3c5" />
                  </div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#88d3c5", marginTop: 4 }}>
                    {systemStatus?.cache?.hit_rate_pct ?? "0.0"}%
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    {systemStatus?.cache?.hits ?? 0} hits / {systemStatus?.cache?.total_requests ?? 0} requests
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Worker Status</span>
                    <Cpu size={15} color={C.accent} />
                  </div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: C.text, marginTop: 4, textTransform: "uppercase" }}>
                    {systemStatus?.worker?.status || "IDLE"}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Loop running: {systemStatus?.worker?.worker_active ? "Active" : "Inactive"}
                  </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "0.72rem", color: C.muted, textTransform: "uppercase" }}>Synced TMDB Movies</span>
                    <TrendingUp size={15} color="#88d3c5" />
                  </div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#88d3c5", marginTop: 4 }}>
                    {systemStatus?.worker?.total_synced_movies ?? 0}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: C.muted, marginTop: 2 }}>
                    Enriched trailers & watch providers
                  </div>
                </div>
              </div>

              {/* Detailed Diagnostics Panels */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
                  gap: 16,
                }}
              >
                {/* Cache Card */}
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "18px 22px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Server size={16} color={C.accent} />
                    <h4 style={{ margin: 0, fontSize: "0.95rem", color: C.text }}>
                      Caching Layer Diagnostics
                    </h4>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: "0.8rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Backend Driver:</span>
                      <strong style={{ color: C.text, fontFamily: "monospace" }}>{systemStatus?.cache?.backend || "in-memory (tttl)"}</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Total Cache Sets:</span>
                      <strong style={{ color: C.text }}>{systemStatus?.cache?.total_sets ?? 0}</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Total Hits:</span>
                      <strong style={{ color: "#88d3c5" }}>{systemStatus?.cache?.hits ?? 0}</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Total Misses:</span>
                      <strong style={{ color: C.muted }}>{systemStatus?.cache?.misses ?? 0}</strong>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: C.muted }}>In-Memory Cache Items:</span>
                      <strong style={{ color: C.text }}>{systemStatus?.cache?.memory_items_count ?? 0} / {systemStatus?.cache?.max_memory_capacity ?? 10000}</strong>
                    </div>
                  </div>
                  <p style={{ margin: "6px 0 0 0", fontSize: "0.75rem", color: C.muted, lineHeight: 1.5 }}>
                    The cache transparently speeds up TMDB API calls, RecSys popularity baselines, and YouTube trailer metadata lookups.
                  </p>
                </div>

                {/* Worker Card */}
                <div
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: `1px solid ${C.border}`,
                    borderRadius: 6,
                    padding: "18px 22px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Clock size={16} color="#88d3c5" />
                    <h4 style={{ margin: 0, fontSize: "0.95rem", color: C.text }}>
                      Ingestion Schedule & Health
                    </h4>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: "0.8rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Worker Daemon:</span>
                      <span style={{ color: systemStatus?.worker?.worker_active ? "#88d3c5" : C.muted, fontWeight: 600 }}>
                        {systemStatus?.worker?.worker_active ? "Online & Polling" : "Offline / Disabled"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Last Sync Run:</span>
                      <span style={{ color: C.text }}>
                        {systemStatus?.worker?.last_run_at ? new Date(systemStatus.worker.last_run_at).toLocaleTimeString() : "Pending"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 6 }}>
                      <span style={{ color: C.muted }}>Next Scheduled Run:</span>
                      <span style={{ color: C.accent }}>
                        {systemStatus?.worker?.next_run_at ? new Date(systemStatus.worker.next_run_at).toLocaleTimeString() : "Every 6 hours"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: C.muted }}>Last Exception:</span>
                      <span style={{ color: systemStatus?.worker?.last_error ? "#e88080" : "#88d3c5" }}>
                        {systemStatus?.worker?.last_error || "None (healthy)"}
                      </span>
                    </div>
                  </div>
                  <p style={{ margin: "6px 0 0 0", fontSize: "0.75rem", color: C.muted, lineHeight: 1.5 }}>
                    The worker crawls TMDB feeds in the background, populates trailers and watch providers, and pre-warms the RecSys engine without blocking user requests.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FORMULAS & THEORY */}
          {activeTab === "formulas" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ marginBottom: 4 }}>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600, margin: 0 }}>
                  Mathematical Metric Definitions & Formulations
                </h3>
                <p style={{ fontSize: "0.8rem", color: C.muted, marginTop: 4 }}>
                  The formal mathematical foundations underlying the offline evaluation harness in{" "}
                  <code>scripts/run_evaluation.py</code>.
                </p>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
                  gap: 16,
                }}
              >
                {(data?.formulas || DEFAULT_BENCHMARKS.formulas).map((f, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${C.border}`,
                      borderRadius: 6,
                      padding: "18px 22px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 10,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ fontSize: "0.95rem", fontWeight: 600, color: C.text }}>
                        {f.name}
                      </span>
                      <span
                        style={{
                          fontSize: "0.74rem",
                          background: "rgba(227,163,78,0.12)",
                          border: "1px solid rgba(227,163,78,0.3)",
                          color: C.accent,
                          padding: "2px 8px",
                          borderRadius: 4,
                          fontFamily: "monospace",
                        }}
                      >
                        {f.symbol}
                      </span>
                    </div>

                    <div
                      style={{
                        background: "rgba(0,0,0,0.35)",
                        border: `1px solid ${C.border}`,
                        borderRadius: 4,
                        padding: "12px 16px",
                        fontFamily: "Courier New, monospace",
                        fontSize: "0.88rem",
                        color: "#88d3c5",
                        letterSpacing: "0.02em",
                      }}
                    >
                      {f.formula}
                    </div>

                    <p style={{ fontSize: "0.8rem", color: C.muted, lineHeight: 1.55, margin: 0 }}>
                      {f.explanation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: "14px 28px",
            borderTop: `1px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "rgba(0,0,0,0.3)",
            fontSize: "0.78rem",
            color: C.muted,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span>Dataset: <strong>MovieLens (ml-latest-small) + TMDB Metadata</strong></span>
            <span>Split: <strong>Leave-Last-5-Out Temporal</strong></span>
          </div>
          <button
            onClick={onClose}
            className="cta-btn"
            style={{
              background: C.accent,
              color: C.bg,
              border: "none",
              padding: "7px 18px",
              borderRadius: 3,
              fontWeight: 600,
              fontSize: "0.82rem",
              cursor: "pointer",
              fontFamily: "'Work Sans', sans-serif",
            }}
          >
            Close Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
