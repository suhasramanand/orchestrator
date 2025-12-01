import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobApi } from '../services/api';
import './JobCreateForm.css';

const JobCreateForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    job_type: 'compute',
    num_tasks: 10,
    work_type: 'cpu_bound',
    work_duration_seconds: 2.0,
    matrix_size: 100,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const parameters: Record<string, any> = {
        work_type: formData.work_type,
        work_duration_seconds: parseFloat(formData.work_duration_seconds.toString()),
      };

      if (formData.work_type === 'matrix_multiply') {
        parameters.matrix_size = parseInt(formData.matrix_size.toString());
      }

      const job = await jobApi.createJob({
        job_type: formData.job_type,
        num_tasks: parseInt(formData.num_tasks.toString()),
        parameters,
      });

      setSuccess(true);
      setTimeout(() => {
        navigate(`/jobs/${job.id}`);
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="job-create-form">
      <div className="card">
        <h2>Create Job</h2>
        
        {error && <div className="error">{error}</div>}
        {success && <div className="success">Job created successfully! Redirecting...</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="job_type">Job Type</label>
            <select
              id="job_type"
              name="job_type"
              value={formData.job_type}
              onChange={handleChange}
              required
            >
              <option value="compute">Compute</option>
              <option value="data_processing">Data Processing</option>
              <option value="ml_inference">ML Inference</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="num_tasks">Number of Tasks</label>
            <input
              type="number"
              id="num_tasks"
              name="num_tasks"
              value={formData.num_tasks}
              onChange={handleChange}
              min="1"
              max="1000"
              required
            />
            <small>Number of parallel tasks to create (1-1000)</small>
          </div>

          <div className="form-group">
            <label htmlFor="work_type">Work Type</label>
            <select
              id="work_type"
              name="work_type"
              value={formData.work_type}
              onChange={handleChange}
              required
            >
              <option value="cpu_bound">CPU Bound</option>
              <option value="io_bound">I/O Bound</option>
              <option value="matrix_multiply">Matrix Multiply</option>
            </select>
            <small>Type of computation to simulate</small>
          </div>

          <div className="form-group">
            <label htmlFor="work_duration_seconds">Work Duration (seconds)</label>
            <input
              type="number"
              id="work_duration_seconds"
              name="work_duration_seconds"
              value={formData.work_duration_seconds}
              onChange={handleChange}
              min="0.1"
              max="60"
              step="0.1"
              required
            />
            <small>Approximate duration for each task</small>
          </div>

          {formData.work_type === 'matrix_multiply' && (
            <div className="form-group">
              <label htmlFor="matrix_size">Matrix Size</label>
              <input
                type="number"
                id="matrix_size"
                name="matrix_size"
                value={formData.matrix_size}
                onChange={handleChange}
                min="10"
                max="1000"
                required
              />
              <small>Size of the square matrix (NxN)</small>
            </div>
          )}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Job'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/')}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JobCreateForm;

