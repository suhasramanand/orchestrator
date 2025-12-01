import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobApi } from '../services/api';
import type { Job, JobStatus } from '../types';
import './JobList.css';

const JobList = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [page, pageSize, searchQuery]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await jobApi.listJobs(page, pageSize, searchQuery);
      setJobs(response.jobs);
      setTotalPages(response.total_pages);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(1); // Reset to first page on search
  };

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
    setPage(1); // Reset to first page on page size change
  };

  const formatJobId = (jobId: string): string => {
    // Show last 8 characters instead of first 8
    return `...${jobId.slice(-8)}`;
  };

  const getStatusClass = (status: JobStatus): string => {
    const statusMap: Record<string, string> = {
      PENDING: 'status-pending',
      CREATING_TASKS: 'status-pending',
      ENQUEUED: 'status-enqueued',
      RUNNING: 'status-running',
      COMPLETED: 'status-completed',
      FAILED: 'status-failed',
      CANCELLED: 'status-pending',
    };
    return statusMap[status] || 'status-pending';
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const getProgress = (job: Job): number => {
    if (job.total_tasks === 0) return 0;
    return Math.round((job.completed_tasks / job.total_tasks) * 100);
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="card">
        <div className="loading">Loading jobs...</div>
      </div>
    );
  }

  return (
    <div className="job-list">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Jobs</h2>
          <Link to="/create" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            + Create Job
          </Link>
        </div>
        
        {/* Search and Page Size Controls */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <input
              type="text"
              placeholder="Search by job ID or type..."
              value={searchQuery}
              onChange={handleSearchChange}
              style={{
                width: '100%',
                padding: '0.625rem 1rem',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                fontSize: '0.9375rem',
                background: 'var(--bg-primary)',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="page-size" style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Show:
            </label>
            <select
              id="page-size"
              value={pageSize}
              onChange={handlePageSizeChange}
              style={{
                padding: '0.625rem 1rem',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                fontSize: '0.9375rem',
                background: 'var(--bg-primary)',
                cursor: 'pointer',
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={30}>30</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>
        
        {error && <div className="error">{error}</div>}
        
        {jobs.length === 0 ? (
          <div className="empty-state">
            <p>No jobs found.</p>
            <Link to="/create" className="btn btn-primary" style={{ marginTop: '1rem', textDecoration: 'none', display: 'inline-block' }}>
              Create your first job
            </Link>
          </div>
        ) : (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Tasks</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <Link to={`/jobs/${job.id}`} className="job-link">
                        {formatJobId(job.id)}
                      </Link>
                    </td>
                    <td>{job.job_type}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      <div className="progress-bar">
                        <div
                          className={`progress-bar-fill ${
                            job.failed_tasks > 0 ? 'error' : ''
                          }`}
                          style={{ width: `${getProgress(job)}%` }}
                        />
                      </div>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'block' }}>
                        {getProgress(job)}%
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>
                        {job.completed_tasks}/{job.total_tasks}
                      </span>
                      {job.failed_tasks > 0 && (
                        <span style={{ color: 'var(--error)', marginLeft: '0.5rem', fontSize: '0.8125rem' }}>
                          ({job.failed_tasks} failed)
                        </span>
                      )}
                    </td>
                    <td>{formatDate(job.created_at)}</td>
                    <td>
                      <Link to={`/jobs/${job.id}`} className="btn btn-secondary">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="pagination">
              <button
                className="btn btn-secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ← Previous
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default JobList;

