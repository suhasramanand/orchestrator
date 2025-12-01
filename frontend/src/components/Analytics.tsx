import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { analyticsApi, OverviewStats, JobsByType, JobsByStatus, TasksByStatus, TimelineData, ProcessingTimeStats } from '../services/analyticsApi';
import './Analytics.css';

const COLORS = ['#0066ff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280'];

const Analytics = () => {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [jobsByType, setJobsByType] = useState<JobsByType[]>([]);
  const [jobsByStatus, setJobsByStatus] = useState<JobsByStatus[]>([]);
  const [tasksByStatus, setTasksByStatus] = useState<TasksByStatus[]>([]);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [processingStats, setProcessingStats] = useState<ProcessingTimeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timelineDays, setTimelineDays] = useState(7);

  useEffect(() => {
    loadAnalytics();
    const interval = setInterval(loadAnalytics, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [timelineDays]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [overviewData, jobsTypeData, jobsStatusData, tasksStatusData, timelineData, processingData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getJobsByType(),
        analyticsApi.getJobsByStatus(),
        analyticsApi.getTasksByStatus(),
        analyticsApi.getTimeline(timelineDays),
        analyticsApi.getProcessingTimeStats(),
      ]);
      
      setOverview(overviewData);
      setJobsByType(jobsTypeData);
      setJobsByStatus(jobsStatusData);
      setTasksByStatus(tasksStatusData);
      setTimeline(timelineData);
      setProcessingStats(processingData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  if (loading && !overview) {
    return (
      <div className="card">
        <div className="loading">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="analytics">
      <div className="card">
        <h2>Analytics Dashboard</h2>
        {error && <div className="error">{error}</div>}
        
        {overview && (
          <>
            {/* Overview Stats */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Jobs</div>
                <div className="stat-value">{overview.total_jobs}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Completed</div>
                <div className="stat-value success">{overview.completed_jobs}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Failed</div>
                <div className="stat-value error">{overview.failed_jobs}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Success Rate</div>
                <div className="stat-value">{overview.success_rate}%</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Tasks</div>
                <div className="stat-value">{overview.total_tasks}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Processing Time</div>
                <div className="stat-value">{formatDuration(overview.avg_processing_time_seconds)}</div>
              </div>
            </div>

            {/* Charts Row 1 */}
            <div className="charts-row">
              <div className="chart-card">
                <h3>Jobs by Type</h3>
                {jobsByType.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={jobsByType}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="job_type" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#0066ff" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">No data</div>
                )}
              </div>

              <div className="chart-card">
                <h3>Jobs by Status</h3>
                {jobsByStatus.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={jobsByStatus as any}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry: any) => `${entry.status}: ${entry.count}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {jobsByStatus.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">No data</div>
                )}
              </div>
            </div>

            {/* Charts Row 2 */}
            <div className="charts-row">
              <div className="chart-card">
                <h3>Tasks by Status</h3>
                {tasksByStatus.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={tasksByStatus as any}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry: any) => `${entry.status}: ${entry.count}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {tasksByStatus.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">No data</div>
                )}
              </div>

              <div className="chart-card">
                <h3>Job Creation Timeline</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <select
                    value={timelineDays}
                    onChange={(e) => setTimelineDays(Number(e.target.value))}
                    style={{
                      padding: '0.5rem',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                    }}
                  >
                    <option value={7}>Last 7 days</option>
                    <option value={14}>Last 14 days</option>
                    <option value={30}>Last 30 days</option>
                  </select>
                </div>
                {timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#0066ff" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">No data</div>
                )}
              </div>
            </div>

            {/* Processing Time Stats */}
            {processingStats && (
              <div className="card" style={{ marginTop: '1.5rem' }}>
                <h3>Processing Time Statistics</h3>
                <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
                  <div className="stat-card">
                    <div className="stat-label">Min</div>
                    <div className="stat-value">{formatDuration(processingStats.min_seconds)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Max</div>
                    <div className="stat-value">{formatDuration(processingStats.max_seconds)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Average</div>
                    <div className="stat-value">{formatDuration(processingStats.avg_seconds)}</div>
                  </div>
                  {processingStats.median_seconds !== null && (
                    <div className="stat-card">
                      <div className="stat-label">Median</div>
                      <div className="stat-value">{formatDuration(processingStats.median_seconds)}</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Analytics;

