
import { useEffect, useState } from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  ChevronDown,
  CircleHelp,
  LayoutDashboard,
  RefreshCw,
  ShieldCheck,
  ShoppingCart,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000/api";

function App() {
  const [summary, setSummary] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [funnel, setFunnel] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [issueFilter, setIssueFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);

  const loadDashboard = async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryRes, anomalyRes, funnelRes, evaluationRes] =
        await Promise.all([
          axios.get(`${API}/dashboard/summary`),
          axios.get(`${API}/anomalies`),
          axios.get(`${API}/analytics/funnel`),
          axios.get(`${API}/analytics/evaluation`),
        ]);

      setSummary(summaryRes.data);
      setAnomalies(anomalyRes.data);
      setFunnel(funnelRes.data);
      setEvaluation(evaluationRes.data);
    } catch (err) {
      console.error("Dashboard API error:", err);
      setError("Unable to load dashboard data. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const money = (value) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value || 0);

  const formatPercent = (value) => {
  const number = Number(value ?? 0);
  return `${(number <= 1 ? number * 100 : number).toFixed(0)}%`;
};

  const metrics = summary
    ? [
        {
          label: "Total Sessions",
          value: summary.total_sessions?.toLocaleString("en-IN"),
          icon: Users,
          color: "blue",
          note: "Customer sessions",
        },
        {
          label: "Total Events",
          value: summary.total_events?.toLocaleString("en-IN"),
          icon: Activity,
          color: "purple",
          note: "Journey interactions",
        },
        {
          label: "Conversions",
          value: summary.total_conversions?.toLocaleString("en-IN"),
          icon: ShoppingCart,
          color: "green",
          note: `${summary.conversion_rate}% conversion rate`,
        },
        {
          label: "Total Revenue",
          value: money(summary.total_revenue),
          icon: BarChart3,
          color: "orange",
          note: "Successful orders",
        },
      ]
    : [];

  const issueLabel = (value) =>
    (value || "unknown").replaceAll("_", " ");
  const filteredAnomalies = anomalies.filter((item) => {
  const matchesIssue =
    issueFilter === "all" || item.issue_type === issueFilter;

  const matchesSeverity =
    severityFilter === "all" || item.severity === severityFilter;

  const matchesStatus =
    statusFilter === "all" || item.resolution_status === statusFilter;

  const search = searchTerm.toLowerCase();

  const matchesSearch =
    !search ||
    item.anomaly_id?.toLowerCase().includes(search) ||
    item.session_id?.toLowerCase().includes(search) ||
    item.detection_reason?.toLowerCase().includes(search);

  return matchesIssue && matchesSeverity && matchesStatus && matchesSearch;
});
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Activity size={23} /></div>
          <div>
            <h2>Journey<span>IQ</span></h2>
            <p>INTELLIGENCE PLATFORM</p>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation">
          <a className="nav-item active" href="#overview">
            <LayoutDashboard size={18} /> Overview
          </a>
          <a className="nav-item" href="#journey">
            <Activity size={18} /> Journey Analytics
          </a>
          <a className="nav-item" href="#investigation">
            <AlertTriangle size={18} /> Anomaly Investigation
          </a>
          <a className="nav-item" href="#evaluation">
            <ShieldCheck size={18} /> Model Evaluation
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>System Operational</strong>
              <small>API connection active</small>
            </div>
          </div>
          <div className="profile">
            <div className="avatar">M</div>
            <div><strong>Administrator</strong><small>Journey Analyst</small></div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="breadcrumb">Workspace / Overview</p>
            <h1>Customer Journey Overview</h1>
            <p className="page-subtitle">
              Monitor customer behavior, conversions and journey exceptions.
            </p>
          </div>
          <button className="refresh-btn" onClick={loadDashboard}>
            <RefreshCw size={16} /> Refresh Data
          </button>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="loading-state">
            <RefreshCw className="spin" size={24} />
            <p>Loading journey intelligence...</p>
          </div>
        ) : summary && (
          <>
            <section className="metric-grid" id="overview">
              {metrics.map((metric) => {
                const Icon = metric.icon;
                return (
                  <div className="metric-card" key={metric.label}>
                    <div className="metric-top">
                      <span>{metric.label}</span>
                      <div className={`metric-icon ${metric.color}`}>
                        <Icon size={20} />
                      </div>
                    </div>
                    <h2>{metric.value}</h2>
                    <p>{metric.note}</p>
                  </div>
                );
              })}
            </section>

            <section className="content-grid">
              <div className="panel journey-panel" id="journey">
                <div className="panel-header">
                  <div>
                    <h3>Journey Outcomes</h3>
                    <p>Distribution of customer session outcomes</p>
                  </div>
                  <span className="panel-tag">ALL SESSIONS</span>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={funnel}>
                      <defs>
                        <linearGradient id="journeyGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#6c8cff" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#6c8cff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#263246" strokeDasharray="4 4" />
                      <XAxis dataKey="stage" stroke="#8995aa" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#8995aa" tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#172235",
                          border: "1px solid #33425a",
                          borderRadius: 10,
                          color: "#fff",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="sessions"
                        stroke="#7795ff"
                        strokeWidth={3}
                        fill="url(#journeyGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="outcome-list">
                  {funnel.map((item) => (
                    <div className="outcome-item" key={item.stage}>
                      <span>{issueLabel(item.stage)}</span>
                      <strong>{item.sessions}</strong>
                      <small>{item.conversion_percentage}%</small>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel anomaly-summary" id="anomalies">
                <div className="panel-header">
                  <div>
                    <h3>Anomaly Monitoring</h3>
                    <p>Detected journey exceptions</p>
                  </div>
                  <AlertTriangle size={20} color="#f0ad58" />
                </div>

                <div className="anomaly-total">
                  <div>
                    <h2>{summary.total_anomalies}</h2>
                    <p>Total detected anomalies</p>
                  </div>
                  <span className="severity-pill">
                    {summary.open_anomalies} Open
                  </span>
                </div>

                <div className="anomaly-list">
                  {anomalies.slice(0, 5).map((item) => (
                    <div className="anomaly-row" key={item.anomaly_id}>
                      <div className="anomaly-indicator">
                        <AlertTriangle size={16} />
                      </div>
                      <div className="anomaly-info">
                        <strong>{issueLabel(item.issue_type)}</strong>
                        <small>Session: {item.session_id || "N/A"}</small>
                      </div>
                      <span className={`severity ${item.severity?.toLowerCase()}`}>
                        {item.severity}
                      </span>
                    </div>
                  ))}
                  {anomalies.length === 0 && <p>No anomalies detected.</p>}
                </div>
              </div>
            </section>

            <section className="bottom-grid" id="evaluation">
              <div className="panel evaluation-panel">
                <div className="panel-header">
                  <div>
                    <h3>Detection Performance</h3>
                    <p>Evaluation against synthetic ground truth</p>
                  </div>
                  <ShieldCheck color="#63d6a0" size={21} />
                </div>
                {evaluation && (
                  <div className="evaluation-grid">
                    <div>
                      <strong>{formatPercent(evaluation.precision)}</strong>
                      <span>Precision</span>
                    </div>
                    <div>
                      <strong>{formatPercent(evaluation.recall)}</strong>
                      <span>Recall</span>
                    </div>
                    <div>
                      <strong>{formatPercent(evaluation.f1_score)}</strong>
                      <span>F1 Score</span>
                    </div>
                  </div>
                )}
                <p className="evaluation-note">
                  Synthetic test results are not proof of real-world detection accuracy.
                </p>
              </div>

              <div className="panel insights-panel">
                <div className="panel-header">
                  <div>
                    <h3>Journey Intelligence</h3>
                    <p>Automated operational highlights</p>
                  </div>
                  <Bot color="#9b8cff" size={22} />
                </div>
                <div className="insight">
                  <div className="insight-icon"><AlertTriangle size={17} /></div>
                  <p>
                    <strong>Exception monitoring active</strong>
                    <span>{summary.total_anomalies} anomalies have been identified by the detection engine.</span>
                  </p>
                </div>
                <div className="insight">
                  <div className="insight-icon green"><Activity size={17} /></div>
                  <p>
                    <strong>Conversion performance</strong>
                    <span>{summary.conversion_rate}% of recorded sessions resulted in conversions.</span>
                  </p>
                </div>
                <div className="insight">
                  <div className="insight-icon purple"><CircleHelp size={17} /></div>
                  <p>
                    <strong>Investigation recommended</strong>
                    <span>Review open anomalies to identify data-quality and journey issues.</span>
                  </p>
                </div>
              </div>
            </section>

<section className="panel investigation-panel" id="investigation">
  <div className="panel-header">
    <div>
      <h3>Anomaly Investigation Center</h3>
      <p>Search, filter and investigate detected customer journey exceptions</p>
    </div>
    <span className="panel-tag">
      {filteredAnomalies.length} RECORDS
    </span>
  </div>

  <div className="filter-toolbar">
    <input
      className="search-input"
      placeholder="Search anomaly ID, session ID or reason..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />

    <select value={issueFilter} onChange={(e) => setIssueFilter(e.target.value)}>
      <option value="all">All anomaly types</option>
      <option value="duplicate_conversion">Duplicate conversion</option>
      <option value="out_of_order_event">Out-of-order event</option>
      <option value="unauthorized_identity_link">Unauthorized identity</option>
      <option value="bot_traffic">Bot traffic</option>
    </select>

    <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
      <option value="all">All severity</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
    </select>

    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
      <option value="all">All statuses</option>
      <option value="open">Open</option>
      <option value="resolved">Resolved</option>
    </select>
  </div>

  <div className="table-wrapper">
    <table className="investigation-table">
      <thead>
        <tr>
          <th>Anomaly ID</th>
          <th>Session ID</th>
          <th>Issue Type</th>
          <th>Severity</th>
          <th>Status</th>
          <th>Investigation</th>
        </tr>
      </thead>

      <tbody>
        {filteredAnomalies.map((item) => (
          <tr key={item.anomaly_id}>
            <td className="id-cell">{item.anomaly_id}</td>
            <td>{item.session_id || "N/A"}</td>
            <td className="issue-cell">
              {item.issue_type.replaceAll("_", " ")}
            </td>
            <td>
              <span className={`severity ${item.severity}`}>
                {item.severity}
              </span>
            </td>
            <td>
              <span className="status-open">
                {item.resolution_status}
              </span>
            </td>
            <td>
              <button
                className="investigate-btn"
                onClick={() => setSelectedAnomaly(item)}
              >
                View details
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>

    {filteredAnomalies.length === 0 && (
      <p className="empty-state">No matching anomalies found.</p>
    )}
  </div>

  {selectedAnomaly && (
    <div className="detail-overlay" onClick={() => setSelectedAnomaly(null)}>
      <div
        className="detail-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-header">
          <div>
            <h3>Anomaly Investigation</h3>
            <p>{selectedAnomaly.anomaly_id}</p>
          </div>
          <button
            className="close-btn"
            onClick={() => setSelectedAnomaly(null)}
          >
            ✕
          </button>
        </div>

        <div className="detail-fields">
          <div><small>Session ID</small><strong>{selectedAnomaly.session_id || "N/A"}</strong></div>
          <div><small>Event ID</small><strong>{selectedAnomaly.event_id || "Not associated"}</strong></div>
          <div><small>Issue Type</small><strong>{selectedAnomaly.issue_type.replaceAll("_", " ")}</strong></div>
          <div><small>Severity</small><strong>{selectedAnomaly.severity}</strong></div>
          <div><small>Resolution Status</small><strong>{selectedAnomaly.resolution_status}</strong></div>
          <div><small>Detection Rule</small><strong>{selectedAnomaly.detection_rule}</strong></div>
        </div>

        <div className="reason-box">
          <h4>Why was this anomaly detected?</h4>
          <p>{selectedAnomaly.detection_reason}</p>
        </div>
      </div>
    </div>
  )}
</section>

            <footer>
              JourneyIQ · Customer Journey Intelligence Platform
              <span>Data powered by FastAPI & PostgreSQL</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
