import axios from 'axios';
import type { Job, JobCreateRequest, JobListResponse, TaskListResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobApi = {
  createJob: async (data: JobCreateRequest): Promise<Job> => {
    const response = await api.post<Job>('/api/v1/jobs', data);
    return response.data;
  },

  getJob: async (jobId: string): Promise<Job> => {
    const response = await api.get<Job>(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  listJobs: async (page: number = 1, pageSize: number = 20, search?: string): Promise<JobListResponse> => {
    const params: any = { page, page_size: pageSize };
    if (search && search.trim()) {
      params.search = search.trim();
    }
    const response = await api.get<JobListResponse>('/api/v1/jobs', { params });
    return response.data;
  },

  getJobTasks: async (jobId: string): Promise<TaskListResponse> => {
    const response = await api.get<TaskListResponse>(`/api/v1/jobs/${jobId}/tasks`);
    return response.data;
  },
};

export default api;

