"""Background tasks."""

from app.workers.celery_app import celery_app


@celery_app.task(name="cleanup_temporary_files")
def cleanup_temporary_files():
    """Clean up temporary files from storage."""
    # Placeholder for Module 2
    return {"status": "completed", "files_cleaned": 0}


@celery_app.task(name="generate_report")
def generate_report(project_id: str):
    """Generate project report."""
    # Placeholder for Module 2
    return {"status": "completed", "project_id": project_id}
