import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { jobApi } from '../services/api';
import type { Job, Task, TaskStatus } from '../types';
import './JobDetail.css';

const JobDetail = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      loadJob();
      loadTasks();
      const interval = setInterval(() => {
        loadJob();
        loadTasks();
      }, 2000); // Refresh every 2 seconds
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const loadJob = async () => {
    if (!jobId) return;
    try {
      const jobData = await jobApi.getJob(jobId);
      setJob(jobData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load job');
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async () => {
    if (!jobId) return;
    try {
      const response = await jobApi.getJobTasks(jobId);
      setTasks(response.tasks);
    } catch (err: any) {
      console.error('Failed to load tasks', err);
    }
  };

  const getStatusClass = (status: TaskStatus | string): string => {
    const statusMap: Record<string, string> = {
      PENDING: 'status-pending',
      CREATING_TASKS: 'status-pending',
      ENQUEUED: 'status-enqueued',
      RUNNING: 'status-running',
      COMPLETED: 'status-completed',
      FAILED: 'status-failed',
      RETRYING: 'status-pending',
      CANCELLED: 'status-pending',
    };
    return statusMap[status] || 'status-pending';
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '-';
    return `${seconds.toFixed(2)}s`;
  };

  if (loading) {
    return (
      <div className="card">
        <div className="loading">Loading job details...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="error">
        {error || 'Job not found'}
        <Link to="/" style={{ display: 'block', marginTop: '1rem' }}>
          Back to Jobs
        </Link>
      </div>
    );
  }

  const progress = job.total_tasks > 0 
    ? Math.round((job.completed_tasks / job.total_tasks) * 100)
    : 0;

  return (
    <div className="job-detail">
      <Link to="/" className="back-link">← Back to Jobs</Link>

      <div className="card">
        <h2 style={{ marginBottom: '1.5rem' }}>Job</h2>
        <div className="job-info">
          <div className="info-row">
            <span className="info-label">Job ID:</span>
            <span className="info-value">{job.id}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Type:</span>
            <span className="info-value">{job.job_type}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Status:</span>
            <span className={`status-badge ${getStatusClass(job.status as any)}`}>
              {job.status}
            </span>
          </div>
          <div className="info-row">
            <span className="info-label">Progress:</span>
            <div className="progress-container">
              <div className="progress-bar">
                <div
                  className={`progress-bar-fill ${
                    job.failed_tasks > 0 ? 'error' : ''
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="progress-text">
                {job.completed_tasks} of {job.total_tasks} tasks completed
                {job.failed_tasks > 0 && (
                  <span style={{ color: 'var(--error)', marginLeft: '0.5rem' }}>
                    ({job.failed_tasks} failed)
                  </span>
                )}
              </span>
            </div>
          </div>
          <div className="info-row">
            <span className="info-label">Created:</span>
            <span className="info-value">{formatDate(job.created_at)}</span>
          </div>
          {job.started_at && (
            <div className="info-row">
              <span className="info-label">Started:</span>
              <span className="info-value">{formatDate(job.started_at)}</span>
            </div>
          )}
          {job.completed_at && (
            <div className="info-row">
              <span className="info-label">Completed:</span>
              <span className="info-value">{formatDate(job.completed_at)}</span>
            </div>
          )}
          {job.error_message && (
            <div className="info-row">
              <span className="info-label">Error:</span>
              <span className="info-value error-text">{job.error_message}</span>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1.5rem' }}>Tasks <span style={{ color: 'var(--text-tertiary)', fontWeight: 400, fontSize: '1rem' }}>({tasks.length})</span></h2>
        {tasks.length === 0 ? (
          <div className="empty-state" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            No tasks found
          </div>
        ) : (
          <div className="tasks-table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Index</th>
                  <th>Task ID</th>
                  <th>Status</th>
                  <th>Retries</th>
                  <th>Processing Time</th>
                  <th>Started</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>{task.task_index}</td>
                    <td className="task-id">...{task.id.slice(-16)}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(task.status)}`}>
                        {task.status}
                      </span>
                    </td>
                    <td>{task.retry_count} / {task.max_retries}</td>
                    <td>{formatDuration(task.processing_time_seconds)}</td>
                    <td>{formatDate(task.started_at)}</td>
                    <td>{formatDate(task.completed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobDetail;

