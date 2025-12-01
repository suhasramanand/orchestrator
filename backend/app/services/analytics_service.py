"""
Analytics service for job and task metrics.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List
import structlog

from app.db.models import Job, Task, JobStatus, TaskStatus

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Service for analytics and metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Get overview statistics."""
        total_jobs = self.db.query(func.count(Job.id)).scalar() or 0
        
        # Job status counts
        job_status_counts = (
            self.db.query(Job.status, func.count(Job.id))
            .group_by(Job.status)
            .all()
        )
        status_map = {status.value: count for status, count in job_status_counts}
        
        # Task status counts
        task_status_counts = (
            self.db.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        task_status_map = {status.value: count for status, count in task_status_counts}
        
        # Completed jobs
        completed_jobs = status_map.get(JobStatus.COMPLETED.value, 0)
        failed_jobs = status_map.get(JobStatus.FAILED.value, 0)
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Total tasks
        total_tasks = self.db.query(func.count(Task.id)).scalar() or 0
        completed_tasks = task_status_map.get(TaskStatus.COMPLETED.value, 0)
        failed_tasks = task_status_map.get(TaskStatus.FAILED.value, 0)
        
        # Average processing time
        avg_processing_time = (
            self.db.query(func.avg(Task.processing_time_seconds))
            .filter(Task.processing_time_seconds.isnot(None))
            .scalar()
        ) or 0
        
        # Total processing time
        total_processing_time = (
            self.db.query(func.sum(Task.processing_time_seconds))
            .filter(Task.processing_time_seconds.isnot(None))
            .scalar()
        ) or 0
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": status_map.get(JobStatus.RUNNING.value, 0),
            "pending_jobs": status_map.get(JobStatus.PENDING.value, 0) + status_map.get(JobStatus.ENQUEUED.value, 0),
            "success_rate": round(success_rate, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": task_status_map.get(TaskStatus.RUNNING.value, 0),
            "pending_tasks": task_status_map.get(TaskStatus.PENDING.value, 0) + task_status_map.get(TaskStatus.ENQUEUED.value, 0),
            "avg_processing_time_seconds": round(avg_processing_time, 2),
            "total_processing_time_seconds": round(total_processing_time, 2),
        }
    
    def get_jobs_by_type(self) -> List[Dict[str, Any]]:
        """Get job counts grouped by job type."""
        results = (
            self.db.query(Job.job_type, func.count(Job.id))
            .group_by(Job.job_type)
            .all()
        )
        return [{"job_type": job_type, "count": count} for job_type, count in results]
    
    def get_jobs_by_status(self) -> List[Dict[str, Any]]:
        """Get job counts grouped by status."""
        results = (
            self.db.query(Job.status, func.count(Job.id))
            .group_by(Job.status)
            .all()
        )
        return [{"status": status.value, "count": count} for status, count in results]
    
    def get_tasks_by_status(self) -> List[Dict[str, Any]]:
        """Get task counts grouped by status."""
        results = (
            self.db.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        return [{"status": status.value, "count": count} for status, count in results]
    
    def get_jobs_timeline(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get job creation timeline for the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get jobs created per day
        results = (
            self.db.query(
                func.date(Job.created_at).label('date'),
                func.count(Job.id).label('count')
            )
            .filter(Job.created_at >= start_date)
            .group_by(func.date(Job.created_at))
            .order_by(func.date(Job.created_at))
            .all()
        )
        
        return [
            {
                "date": date.isoformat() if isinstance(date, datetime) else str(date),
                "count": count
            }
            for date, count in results
        ]
    
    def get_processing_time_stats(self) -> Dict[str, Any]:
        """Get processing time statistics."""
        # Get min, max, avg
        stats = (
            self.db.query(
                func.min(Task.processing_time_seconds).label('min'),
                func.max(Task.processing_time_seconds).label('max'),
                func.avg(Task.processing_time_seconds).label('avg')
            )
            .filter(Task.processing_time_seconds.isnot(None))
            .first()
        )
        
        # Calculate median manually (SQLite doesn't support percentile_cont)
        all_times = (
            self.db.query(Task.processing_time_seconds)
            .filter(Task.processing_time_seconds.isnot(None))
            .order_by(Task.processing_time_seconds)
            .all()
        )
        
        median = None
        if all_times:
            times = [t[0] for t in all_times]
            n = len(times)
            if n > 0:
                if n % 2 == 0:
                    median = (times[n//2 - 1] + times[n//2]) / 2
                else:
                    median = times[n//2]
        
        if stats and stats.min is not None:
            return {
                "min_seconds": round(stats.min, 2),
                "max_seconds": round(stats.max, 2),
                "avg_seconds": round(stats.avg or 0, 2),
                "median_seconds": round(median, 2) if median is not None else None,
            }
        return {
            "min_seconds": 0,
            "max_seconds": 0,
            "avg_seconds": 0,
            "median_seconds": None,
        }
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent jobs with basic info."""
        jobs = (
            self.db.query(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status.value,
                "total_tasks": job.total_tasks,
                "completed_tasks": job.completed_tasks,
                "failed_tasks": job.failed_tasks,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ]

