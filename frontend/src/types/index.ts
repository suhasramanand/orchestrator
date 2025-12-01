export enum JobStatus {
  PENDING = 'PENDING',
  CREATING_TASKS = 'CREATING_TASKS',
  ENQUEUED = 'ENQUEUED',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum TaskStatus {
  PENDING = 'PENDING',
  ENQUEUED = 'ENQUEUED',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
}

export interface Job {
  id: string;
  job_type: string;
  status: JobStatus;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  parameters: Record<string, any> | null;
  created_at: string;
  updated_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface Task {
  id: string;
  job_id: string;
  status: TaskStatus;
  task_index: number;
  retry_count: number;
  max_retries: number;
  parameters: Record<string, any> | null;
  result: Record<string, any> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  processing_time_seconds: number | null;
}

export interface JobCreateRequest {
  job_type: string;
  num_tasks: number;
  parameters?: Record<string, any>;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

