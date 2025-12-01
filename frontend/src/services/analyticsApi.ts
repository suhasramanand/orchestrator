import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface OverviewStats {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  running_jobs: number;
  pending_jobs: number;
  success_rate: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  pending_tasks: number;
  avg_processing_time_seconds: number;
  total_processing_time_seconds: number;
}

export interface JobsByType {
  job_type: string;
  count: number;
}

export interface JobsByStatus {
  status: string;
  count: number;
}

export interface TasksByStatus {
  status: string;
  count: number;
}

export interface TimelineData {
  date: string;
  count: number;
}

export interface ProcessingTimeStats {
  min_seconds: number;
  max_seconds: number;
  avg_seconds: number;
  median_seconds: number | null;
}

export interface RecentJob {
  id: string;
  job_type: string;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  created_at: string | null;
  completed_at: string | null;
}

export const analyticsApi = {
  getOverview: async (): Promise<OverviewStats> => {
    const response = await api.get<OverviewStats>('/api/v1/analytics/overview');
    return response.data;
  },

  getJobsByType: async (): Promise<JobsByType[]> => {
    const response = await api.get<JobsByType[]>('/api/v1/analytics/jobs-by-type');
    return response.data;
  },

  getJobsByStatus: async (): Promise<JobsByStatus[]> => {
    const response = await api.get<JobsByStatus[]>('/api/v1/analytics/jobs-by-status');
    return response.data;
  },

  getTasksByStatus: async (): Promise<TasksByStatus[]> => {
    const response = await api.get<TasksByStatus[]>('/api/v1/analytics/tasks-by-status');
    return response.data;
  },

  getTimeline: async (days: number = 7): Promise<TimelineData[]> => {
    const response = await api.get<TimelineData[]>('/api/v1/analytics/timeline', {
      params: { days },
    });
    return response.data;
  },

  getProcessingTimeStats: async (): Promise<ProcessingTimeStats> => {
    const response = await api.get<ProcessingTimeStats>('/api/v1/analytics/processing-time-stats');
    return response.data;
  },

  getRecentJobs: async (limit: number = 10): Promise<RecentJob[]> => {
    const response = await api.get<RecentJob[]>('/api/v1/analytics/recent-jobs', {
      params: { limit },
    });
    return response.data;
  },
};

