"""Repository for Task model operations."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task, TaskStatus
from ...utils.logger import get_logger

logger = get_logger(__name__)


class TaskRepository:
    """Repository for managing task records."""
    
    @staticmethod
    def create_task(
        session: Session,
        task_type: str,
        video_url_id: Optional[int] = None
    ) -> Task:
        """Create a new task.
        
        Args:
            session: Database session
            task_type: Type of task (e.g., 'analysis', 'generation')
            video_url_id: Optional related video URL ID
            
        Returns:
            Created Task instance
        """
        task = Task(
            task_type=task_type,
            video_url_id=video_url_id,
            status=TaskStatus.PENDING
        )
        
        session.add(task)
        session.flush()
        
        logger.info(f"Created task: {task_type} (ID: {task.id})")
        return task
    
    @staticmethod
    def get_by_id(session: Session, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return session.get(Task, task_id)
    
    @staticmethod
    def get_by_status(
        session: Session,
        status: TaskStatus,
        task_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Get tasks by status.
        
        Args:
            session: Database session
            status: Task status to filter by
            task_type: Optional task type filter
            limit: Maximum number of results
            
        Returns:
            List of Task instances
        """
        stmt = select(Task).where(Task.status == status)
        
        if task_type:
            stmt = stmt.where(Task.task_type == task_type)
        
        stmt = stmt.order_by(Task.created_at.asc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_pending_tasks(
        session: Session,
        task_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Get pending tasks.
        
        Args:
            session: Database session
            task_type: Optional task type filter
            limit: Maximum number of results
            
        Returns:
            List of pending Task instances
        """
        return TaskRepository.get_by_status(session, TaskStatus.PENDING, task_type, limit)
    
    @staticmethod
    def get_failed_tasks(
        session: Session,
        task_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Get failed tasks.
        
        Args:
            session: Database session
            task_type: Optional task type filter
            limit: Maximum number of results
            
        Returns:
            List of failed Task instances
        """
        return TaskRepository.get_by_status(session, TaskStatus.FAILED, task_type, limit)
    
    @staticmethod
    def update_task_status(
        session: Session,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None,
        result: Optional[dict] = None
    ) -> Optional[Task]:
        """Update task status.
        
        Args:
            session: Database session
            task_id: Task ID
            status: New status
            error_message: Optional error message if status is FAILED
            result: Optional result data
            
        Returns:
            Updated Task instance or None if not found
        """
        task = session.get(Task, task_id)
        
        if task:
            task.status = status
            
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow()
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.utcnow()
            
            if error_message:
                task.error_message = error_message
            
            if result:
                task.result = result
            
            session.flush()
            logger.info(f"Updated task {task_id} status to {status.value}")
        
        return task
    
    @staticmethod
    def update_progress(
        session: Session,
        task_id: int,
        progress: float
    ) -> Optional[Task]:
        """Update task progress.
        
        Args:
            session: Database session
            task_id: Task ID
            progress: Progress percentage (0.0 to 1.0)
            
        Returns:
            Updated Task instance or None if not found
        """
        task = session.get(Task, task_id)
        
        if task:
            task.progress = max(0.0, min(1.0, progress))
            session.flush()
        
        return task
    
    @staticmethod
    def increment_retry_count(session: Session, task_id: int) -> Optional[Task]:
        """Increment retry count for a task.
        
        Args:
            session: Database session
            task_id: Task ID
            
        Returns:
            Updated Task instance or None if not found
        """
        task = session.get(Task, task_id)
        
        if task:
            task.retry_count += 1
            session.flush()
            logger.info(f"Incremented retry count for task {task_id} to {task.retry_count}")
        
        return task
    
    @staticmethod
    def get_tasks_by_video(
        session: Session,
        video_url_id: int
    ) -> List[Task]:
        """Get all tasks for a specific video.
        
        Args:
            session: Database session
            video_url_id: Video URL ID
            
        Returns:
            List of Task instances
        """
        stmt = select(Task).where(Task.video_url_id == video_url_id).order_by(Task.created_at.desc())
        result = session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_running_tasks(
        session: Session,
        task_type: Optional[str] = None
    ) -> List[Task]:
        """Get currently running tasks.
        
        Args:
            session: Database session
            task_type: Optional task type filter
            
        Returns:
            List of running Task instances
        """
        return TaskRepository.get_by_status(session, TaskStatus.RUNNING, task_type)
    
    @staticmethod
    def cancel_task(session: Session, task_id: int) -> Optional[Task]:
        """Cancel a task.
        
        Args:
            session: Database session
            task_id: Task ID
            
        Returns:
            Cancelled Task instance or None if not found
        """
        return TaskRepository.update_task_status(
            session,
            task_id,
            TaskStatus.CANCELLED
        )
    
    @staticmethod
    def delete(session: Session, task_id: int) -> bool:
        """Delete a task record.
        
        Args:
            session: Database session
            task_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        task = session.get(Task, task_id)
        
        if task:
            session.delete(task)
            session.flush()
            logger.info(f"Deleted task {task_id}")
            return True
        
        return False
