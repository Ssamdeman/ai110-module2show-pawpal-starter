import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Priority, Species


def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species=Species.DOG)
    assert len(pet.tasks) == 0
    pet.tasks.append(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH))
    assert len(pet.tasks) == 1
    pet.tasks.append(Task(title="Walk", duration_minutes=20, priority=Priority.MEDIUM))
    assert len(pet.tasks) == 2
