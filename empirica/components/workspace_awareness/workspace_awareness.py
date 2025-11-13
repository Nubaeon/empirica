#!/usr/bin/env python3
"""
🧭 Workspace Awareness Module
Intelligent workspace navigation and persistent awareness for AI systems

This module provides comprehensive workspace awareness capabilities including:
- Digital map management for navigational intelligence
- Persistent awareness state tracking
- Task and project organization
- Workspace intelligence and navigation
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class DigitalMap:
    """Digital map structure for workspace navigation"""
    project_name: str
    description: str
    last_updated: str
    map_version: str
    areas: list

class WorkspaceNavigator:
    """Workspace Navigation and Awareness system"""
    
    def __init__(self, map_file_path: str = "digital_workspace_map.json"):
        """
        Initialize the Workspace Navigator
        
        Args:
            map_file_path (str): Path to the digital map file
        """
        self.map_file_path = Path(map_file_path)
        self.digital_map = self._load_map()
    
    def _load_map(self) -> DigitalMap:
        """Load the digital map from the specified JSON file"""
        if self.map_file_path.exists():
            try:
                map_data = json.loads(self.map_file_path.read_text())
                return DigitalMap(**map_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding Digital Map JSON from {self.map_file_path}: {e}. Initializing empty map.")
                return self._initialize_empty_map()
        else:
            print(f"Digital Map file not found at {self.map_file_path}. Initializing empty map.")
            return self._initialize_empty_map()
    
    def _initialize_empty_map(self) -> DigitalMap:
        """Initialize an empty digital map structure"""
        return DigitalMap(
            project_name="AI Self-Aware Kit Development",
            description="A living map of our collaborative development workspace.",
            last_updated=datetime.now().isoformat(),
            map_version="1.0.0",
            areas=[]
        )
    
    def _save_map(self):
        """Save the current state of the digital map to the file"""
        # Convert dataclass to dictionary for JSON serialization
        map_dict = {
            'project_name': self.digital_map.project_name,
            'description': self.digital_map.description,
            'last_updated': self.digital_map.last_updated,
            'map_version': self.digital_map.map_version,
            'areas': self.digital_map.areas
        }
        self.map_file_path.write_text(json.dumps(map_dict, indent=2))
    
    def get_current_status(self) -> Dict[str, Any]:
        """Return the current status of the digital map"""
        completed_areas = len([a for a in self.digital_map.areas if a.get("status") == "completed"])
        in_progress_areas = len([a for a in self.digital_map.areas if a.get("status") == "in_progress"])
        
        return {
            "project_name": self.digital_map.project_name,
            "status": "Operational",
            "completed_areas": completed_areas,
            "in_progress_areas": in_progress_areas,
            "last_updated": self.digital_map.last_updated
        }
    
    def find_next_task(self, assigned_to: str = "AI") -> Optional[Dict[str, Any]]:
        """Find the next task that is 'undiscovered' or 'in_progress' and assigned to the specified AI."""
        for area in self.digital_map.areas:
            for sub_area in area.get("sub_areas", []):
                if sub_area.get("assigned_ai") == assigned_to:
                    for task in sub_area.get("tasks", []):
                        if task.get("status") == "in_progress":
                            return task
                    for task in sub_area.get("tasks", []):
                        if task.get("status") == "undiscovered":
                            return task
        return None
    
    def update_task_status(self, task_id: str, new_status: str, last_log_entry: str = "") -> bool:
        """Update the status of a specific task"""
        for area in self.digital_map.areas:
            for sub_area in area.get("sub_areas", []):
                for task in sub_area.get("tasks", []):
                    if task.get("id") == task_id:
                        task["status"] = new_status
                        if last_log_entry:
                            task["last_log_entry"] = last_log_entry
                        self.digital_map.last_updated = datetime.now().isoformat()
                        self._save_map()
                        return True
        return False
    
    def add_task(self, area_id: str, sub_area_id: str, task: Dict[str, Any]) -> bool:
        """Add a new task to a specified sub-area"""
        for area in self.digital_map.areas:
            if area.get("id") == area_id:
                for sub_area in area.get("sub_areas", []):
                    if sub_area.get("id") == sub_area_id:
                        sub_area["tasks"].append(task)
                        self.digital_map.last_updated = datetime.now().isoformat()
                        self._save_map()
                        return True
        return False
    
    def add_sub_area(self, area_id: str, sub_area: Dict[str, Any]) -> bool:
        """Add a new sub-area to a specified area"""
        for area in self.digital_map.areas:
            if area.get("id") == area_id:
                area["sub_areas"].append(sub_area)
                self.digital_map.last_updated = datetime.now().isoformat()
                self._save_map()
                return True
        return False
    
    def add_area(self, area: Dict[str, Any]) -> bool:
        """Add a new top-level area to the digital map"""
        self.digital_map.areas.append(area)
        self.digital_map.last_updated = datetime.now().isoformat()
        self._save_map()
        return True
    
    def get_workspace_intelligence(self) -> Dict[str, Any]:
        """Get comprehensive workspace intelligence"""
        total_areas = len(self.digital_map.areas)
        total_sub_areas = sum(len(area.get("sub_areas", [])) for area in self.digital_map.areas)
        total_tasks = sum(
            len(task)
            for area in self.digital_map.areas
            for sub_area in area.get("sub_areas", [])
            for task in [sub_area.get("tasks", [])]
        )
        
        # Count tasks by status
        status_counts = {}
        for area in self.digital_map.areas:
            for sub_area in area.get("sub_areas", []):
                for task in sub_area.get("tasks", []):
                    status = task.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "map_version": self.digital_map.map_version,
            "last_updated": self.digital_map.last_updated,
            "total_areas": total_areas,
            "total_sub_areas": total_sub_areas,
            "total_tasks": total_tasks,
            "tasks_by_status": status_counts,
            "project_name": self.digital_map.project_name
        }
