import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Activity,
  CheckCircle2,
  Clock3,
  Mail,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  Target,
  Users,
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const emptyLead = {
  name: "",
  email: "",
  company: "",
  title: "",
  industry: "",
};

const statusTone = {
  pending: "muted",
  outreach_sent: "active",
  replied_interested: "good",
  qualified: "good",
  booked: "good",
};

function App() {
  const [apiKey, setApiKey] = useState("");
  const [summary, setSummary] = useState(null);
  const [leads, setLeads] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [activities, setActivities] = useState([]);
  const [leadForm, setLeadForm] = useState(emptyLead);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const client = useMemo(() => {
    const headers = apiKey ? { "x-api-key": apiKey } : {};
    return axios.create({ baseURL: API_URL, headers });
  }, [apiKey]);

  async function loadAll() {
    setBusy(true);
    setMessage("");
    try {
      const [summaryRes, leadsRes, draftsRes, jobsRes, activitiesRes] = await Promise.all([
        client.get("/dashboard/summary"),
        client.get("/leads?limit=100"),
        client.get("/drafts"),
        client.get("/jobs"),
        client.get("/activities"),
      ]);
      setSummary(summaryRes.data);
      setLeads(leadsRes.data);
      setDrafts(draftsRes.data);
      setJobs(jobsRes.data);
      setActivities(activitiesRes.data);
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to load dashboard.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, [client]);

  async function createLead(event) {
    event.preventDefault();
    setMessage("");
    try {
      await client.post("/leads", leadForm);
      setLeadForm(emptyLead);
      setMessage("Lead added.");
      await loadAll();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to create lead.");
    }
  }

  async function generateDraft(leadId) {
    setMessage("");
    try {
      await client.post("/drafts/generate", null, { params: { lead_id: leadId } });
      setMessage("Draft generated.");
      await loadAll();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to generate draft.");
    }
  }

  async function approveDraft(draftId) {
    setMessage("");
    try {
      await client.post(`/drafts/${draftId}/approve`, { approved: true });
      setMessage("Draft approved and queued.");
      await loadAll();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to approve draft.");
    }
  }

  async function scoreLead(leadId) {
    setMessage("");
    try {
      await client.post(`/leads/${leadId}/score`);
      setMessage("Lead scored.");
      await loadAll();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to score lead.");
    }
  }

  async function queueFollowUp(leadId) {
    setMessage("");
    try {
      await client.post("/jobs/follow-ups", {
        lead_id: leadId,
        reason: "operator_follow_up",
        channel: "email",
      });
      setMessage("Follow-up queued.");
      await loadAll();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Unable to queue follow-up.");
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <h1>Autonomous Sales Console</h1>
          <p>Lead intake, draft review, queue control, and operator oversight.</p>
        </div>
        <div className="topbar-actions">
          <label className="api-key-field">
            <span>API Key</span>
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Optional for local mode"
            />
          </label>
          <button className="icon-button" onClick={loadAll} disabled={busy} title="Refresh">
            <RefreshCw size={18} className={busy ? "spin" : ""} />
          </button>
        </div>
      </header>

      {message ? <div className="message-bar">{message}</div> : null}

      <section className="hero-grid">
        <StatCard icon={Users} label="Leads" value={summary?.totals?.leads ?? 0} />
        <StatCard icon={Mail} label="Replies" value={summary?.totals?.replied ?? 0} />
        <StatCard icon={Target} label="Qualified" value={summary?.totals?.qualified ?? 0} />
        <StatCard icon={Clock3} label="Queued Jobs" value={summary?.totals?.jobs_queued ?? 0} />
      </section>

      <main className="workspace">
        <section className="panel panel-wide">
          <div className="panel-header">
            <div>
              <h2>Pipeline</h2>
              <p>Work the list, generate messages, and push deals forward.</p>
            </div>
          </div>
          <div className="table-grid">
            <div className="table-head">
              <span>Lead</span>
              <span>Status</span>
              <span>Score</span>
              <span>Actions</span>
            </div>
            {leads.map((lead) => (
              <div className="table-row" key={lead.id}>
                <div>
                  <strong>{lead.company}</strong>
                  <div className="subtle">{lead.name || "Unknown"} | {lead.title || "No title"}</div>
                </div>
                <span className={`status-pill ${statusTone[lead.status] || "muted"}`}>{lead.status}</span>
                <span>{lead.qualification_score?.toFixed?.(1) || "-"}</span>
                <div className="row-actions">
                  <button className="ghost-button" onClick={() => generateDraft(lead.id)} title="Generate draft">
                    <Sparkles size={16} />
                  </button>
                  <button className="ghost-button" onClick={() => scoreLead(lead.id)} title="Score lead">
                    <Target size={16} />
                  </button>
                  <button className="ghost-button" onClick={() => queueFollowUp(lead.id)} title="Queue follow-up">
                    <Clock3 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>New Lead</h2>
              <p>Add operators, founders, or targets manually.</p>
            </div>
            <Plus size={18} />
          </div>
          <form className="form-grid" onSubmit={createLead}>
            <input value={leadForm.company} onChange={(e) => setLeadForm({ ...leadForm, company: e.target.value })} placeholder="Company" required />
            <input value={leadForm.name} onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })} placeholder="Contact name" required />
            <input value={leadForm.email} onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })} placeholder="Email" required />
            <input value={leadForm.title} onChange={(e) => setLeadForm({ ...leadForm, title: e.target.value })} placeholder="Title" />
            <input value={leadForm.industry} onChange={(e) => setLeadForm({ ...leadForm, industry: e.target.value })} placeholder="Industry" />
            <button className="primary-button" type="submit">
              <Send size={16} />
              Add Lead
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Draft Queue</h2>
              <p>Approve generated copy before it reaches outbound.</p>
            </div>
            <Mail size={18} />
          </div>
          <div className="stack-list">
            {drafts.slice(0, 6).map((draft) => (
              <div className="stack-item" key={draft.id}>
                <div>
                  <strong>{draft.email_subject}</strong>
                  <div className="subtle">Lead #{draft.lead_id} | {draft.status}</div>
                </div>
                <button className="ghost-button wide" onClick={() => approveDraft(draft.id)}>
                  <CheckCircle2 size={16} />
                  Approve
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Jobs</h2>
              <p>Queued sends and follow-ups.</p>
            </div>
            <Clock3 size={18} />
          </div>
          <div className="stack-list">
            {jobs.slice(0, 6).map((job) => (
              <div className="stack-item" key={job.id}>
                <div>
                  <strong>{job.type.replaceAll("_", " ")}</strong>
                  <div className="subtle">Lead #{job.lead_id || "-"} | {job.status}</div>
                </div>
                <span className="subtle">{job.send_at ? "Scheduled" : "Immediate"}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Activity</h2>
              <p>Operator and automation trail.</p>
            </div>
            <Activity size={18} />
          </div>
          <div className="activity-list">
            {activities.slice(0, 8).map((activity, index) => (
              <div className="activity-row" key={`${activity.timestamp}-${index}`}>
                <span className="activity-type">{activity.type.replaceAll("_", " ")}</span>
                <span>{activity.message}</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">
        <Icon size={18} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default App;
