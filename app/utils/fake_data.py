from datetime import datetime, timedelta
from app.models.project import Project
from app.models.task import Task
from app.models.tag import Tag


def generate_mock_data():
    projects = [Project(id=1, name="Demo Project")]
    tasks = [
        Task(
            id=1,
            project_id=1,
            name="First Task",
            due_date=datetime.now() + timedelta(days=7),
        )
    ]
    tags = [Tag(id=1, name="Important", linked_type="task", linked_id=1)]
    return projects, tasks, tags
