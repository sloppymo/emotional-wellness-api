"""
Project Manager for EmpathyFine
Handles project creation, saving, loading, and management using SQLite

This module provides the core project management functionality for EmpathyFine.
It uses SQLite for persistent storage of project configurations, training history,
and evaluation results. The ProjectConfig dataclass defines the structure of
a project with empathy-specific settings.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)


@dataclass
class ProjectConfig:
    """
    Configuration for an EmpathyFine project.
    
    This dataclass holds all the configuration parameters for a project,
    including model selection, training settings, evaluation metrics,
    and empathy-specific configurations.
    
    Attributes:
        name: Project name (used for directory and database naming)
        description: Optional project description
        base_model: The base model to fine-tune (e.g., DialoGPT, BlenderBot)
        framework: ML framework to use ("huggingface" or "openai")
        dataset_path: Path to the training dataset
        created_at: ISO format timestamp of project creation
        updated_at: ISO format timestamp of last update
        training_config: Dictionary of training hyperparameters
        evaluation_config: Dictionary of evaluation settings
        empathy_settings: Dictionary of empathy-specific configurations
    """
    name: str
    description: str = ""
    base_model: str = "microsoft/DialoGPT-medium"
    framework: str = "huggingface"  # huggingface or openai
    dataset_path: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    # Training configuration
    training_config: Dict[str, Any] = None
    
    # Evaluation configuration
    evaluation_config: Dict[str, Any] = None
    
    # Empathy-specific settings
    empathy_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """
        Initialize default values after dataclass initialization.
        
        Sets timestamps and default configurations if not provided.
        This ensures all projects have valid default settings.
        """
        # Set timestamps if not provided
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
            
        # Set default training configuration
        if self.training_config is None:
            self.training_config = {
                "epochs": 3,
                "batch_size": 4,
                "learning_rate": 5e-5,
                "lora_rank": 8,  # LoRA specific
                "lora_alpha": 16,  # LoRA specific
                "lora_dropout": 0.1  # LoRA specific
            }
            
        # Set default evaluation configuration
        if self.evaluation_config is None:
            self.evaluation_config = {
                "empathy_threshold": 0.7,  # Minimum empathy score
                "bias_categories": ["gender", "race", "age", "religion", "socioeconomic"],
                "evaluation_metrics": ["empathy_score", "bias_score", "coherence", "fluency"]
            }
            
        # Set default empathy settings
        if self.empathy_settings is None:
            self.empathy_settings = {
                "emotion_tags": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
                "empathy_dimensions": ["cognitive", "emotional", "compassionate"],
                "persona_templates": []  # Custom personas for training
            }


class ProjectManager:
    """
    Manages EmpathyFine projects with SQLite backend.
    
    This class handles all project-related operations including creation,
    loading, saving, and deletion. It maintains a SQLite database for
    each project to store configuration, training history, and results.
    
    The workspace directory structure:
    workspace/
    ├── project1/
    │   ├── project.json      # Project metadata
    │   ├── project1.db       # SQLite database
    │   ├── datasets/         # Dataset files
    │   ├── models/           # Saved models
    │   ├── checkpoints/      # Training checkpoints
    │   ├── exports/          # Exported models
    │   ├── logs/             # Training logs
    │   └── evaluations/      # Evaluation results
    └── project2/
        └── ...
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        """
        Initialize the project manager.
        
        Args:
            workspace_dir: Path to the workspace directory where all projects are stored
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)  # Create workspace if it doesn't exist
        self.current_project: Optional[ProjectConfig] = None
        self.db_path: Optional[Path] = None
        
    def create_project(self, config: ProjectConfig) -> bool:
        """
        Create a new project with the given configuration.
        
        This method:
        1. Creates the project directory structure
        2. Initializes the SQLite database
        3. Saves the project configuration
        4. Creates a project.json metadata file
        
        Args:
            config: ProjectConfig object with project settings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create project directory
            project_dir = self.workspace_dir / config.name
            project_dir.mkdir(exist_ok=True)
            
            # Create subdirectories for organization
            for subdir in ["datasets", "models", "checkpoints", "exports", "logs", "evaluations"]:
                (project_dir / subdir).mkdir(exist_ok=True)
            
            # Create SQLite database
            self.db_path = project_dir / f"{config.name}.db"
            self._init_database()
            
            # Save project configuration to database
            self._save_config(config)
            
            # Create project metadata file for easy access
            metadata_path = project_dir / "project.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            self.current_project = config
            logger.info(f"Created project: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            return False
    
    def load_project(self, project_name: str) -> Optional[ProjectConfig]:
        """
        Load an existing project by name.
        
        Args:
            project_name: Name of the project to load
            
        Returns:
            ProjectConfig object if successful, None otherwise
        """
        try:
            project_dir = self.workspace_dir / project_name
            if not project_dir.exists():
                logger.error(f"Project directory not found: {project_name}")
                return None
            
            # Load from metadata file
            metadata_path = project_dir / "project.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    config_dict = json.load(f)
                    config = ProjectConfig(**config_dict)
                    
                self.current_project = config
                self.db_path = project_dir / f"{project_name}.db"
                logger.info(f"Loaded project: {project_name}")
                return config
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load project: {str(e)}")
            return None
    
    def save_project(self) -> bool:
        """
        Save the current project state.
        
        Updates both the project.json file and the database configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_project:
            logger.error("No project loaded")
            return False
            
        try:
            # Update timestamp
            self.current_project.updated_at = datetime.now().isoformat()
            
            # Update metadata file
            project_dir = self.workspace_dir / self.current_project.name
            metadata_path = project_dir / "project.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(self.current_project), f, indent=2)
            
            # Update database
            self._save_config(self.current_project)
            
            logger.info(f"Saved project: {self.current_project.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project: {str(e)}")
            return False
    
    def list_projects(self) -> List[str]:
        """
        List all available projects in the workspace.
        
        Returns:
            List of project names sorted alphabetically
        """
        projects = []
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and (item / "project.json").exists():
                projects.append(item.name)
        return sorted(projects)
    
    def delete_project(self, project_name: str) -> bool:
        """
        Delete a project and all its associated files.
        
        Args:
            project_name: Name of the project to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project_dir = self.workspace_dir / project_name
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir)
                logger.info(f"Deleted project: {project_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete project: {str(e)}")
            return False
    
    def _init_database(self):
        """
        Initialize SQLite database schema.
        
        Creates tables for:
        - project_config: Stores project configuration
        - training_history: Records training metrics over time
        - evaluation_results: Stores evaluation results
        - dataset_examples: Caches dataset examples with annotations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Project configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_config (
                id INTEGER PRIMARY KEY,
                config TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Training history table - stores metrics during training
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                epoch INTEGER,
                step INTEGER,
                loss REAL,
                accuracy REAL,
                learning_rate REAL,
                metadata TEXT
            )
        """)
        
        # Evaluation results table - stores model evaluation results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_checkpoint TEXT,
                empathy_score REAL,
                bias_score REAL,
                coherence_score REAL,
                fluency_score REAL,
                detailed_results TEXT
            )
        """)
        
        # Dataset examples table - caches annotated dataset examples
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dataset_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context TEXT NOT NULL,
                response TEXT NOT NULL,
                emotion_tags TEXT,
                empathy_dimension TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _save_config(self, config: ProjectConfig):
        """
        Save configuration to database.
        
        Updates existing configuration or creates new one.
        
        Args:
            config: ProjectConfig object to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_json = json.dumps(asdict(config))
        
        # Check if config exists
        cursor.execute("SELECT id FROM project_config LIMIT 1")
        exists = cursor.fetchone()
        
        if exists:
            # Update existing configuration
            cursor.execute("""
                UPDATE project_config 
                SET config = ?, updated_at = ?
                WHERE id = ?
            """, (config_json, config.updated_at, exists[0]))
        else:
            # Insert new configuration
            cursor.execute("""
                INSERT INTO project_config (config, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (config_json, config.created_at, config.updated_at))
        
        conn.commit()
        conn.close()
    
    def add_training_metric(self, epoch: int, step: int, loss: float, 
                           accuracy: float = None, learning_rate: float = None,
                           metadata: Dict = None):
        """
        Add a training metric entry to the database.
        
        This method is called during training to record progress.
        
        Args:
            epoch: Current training epoch
            step: Current training step
            loss: Training loss value
            accuracy: Optional accuracy metric
            learning_rate: Current learning rate
            metadata: Additional metadata as dictionary
        """
        if not self.db_path:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO training_history 
            (timestamp, epoch, step, loss, accuracy, learning_rate, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            epoch,
            step,
            loss,
            accuracy,
            learning_rate,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
    
    def add_evaluation_result(self, model_checkpoint: str, empathy_score: float,
                             bias_score: float = None, coherence_score: float = None,
                             fluency_score: float = None, detailed_results: Dict = None):
        """
        Add an evaluation result to the database.
        
        Records the performance metrics of a model checkpoint.
        
        Args:
            model_checkpoint: Path to the model checkpoint
            empathy_score: Primary empathy score (0-1)
            bias_score: Bias detection score (0-1, lower is better)
            coherence_score: Response coherence score (0-1)
            fluency_score: Language fluency score (0-1)
            detailed_results: Detailed results as dictionary
        """
        if not self.db_path:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evaluation_results 
            (timestamp, model_checkpoint, empathy_score, bias_score, 
             coherence_score, fluency_score, detailed_results)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            model_checkpoint,
            empathy_score,
            bias_score,
            coherence_score,
            fluency_score,
            json.dumps(detailed_results) if detailed_results else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_training_history(self) -> List[Dict]:
        """
        Retrieve training history from database.
        
        Returns:
            List of training metric dictionaries ordered by timestamp
        """
        if not self.db_path:
            return []
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, epoch, step, loss, accuracy, learning_rate, metadata
            FROM training_history
            ORDER BY timestamp
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "epoch": row[1],
                "step": row[2],
                "loss": row[3],
                "accuracy": row[4],
                "learning_rate": row[5],
                "metadata": json.loads(row[6]) if row[6] else None
            })
        
        conn.close()
        return results
    
    def get_evaluation_history(self) -> List[Dict]:
        """
        Retrieve evaluation history from database.
        
        Returns:
            List of evaluation result dictionaries ordered by timestamp (newest first)
        """
        if not self.db_path:
            return []
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, model_checkpoint, empathy_score, bias_score,
                   coherence_score, fluency_score, detailed_results
            FROM evaluation_results
            ORDER BY timestamp DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "model_checkpoint": row[1],
                "empathy_score": row[2],
                "bias_score": row[3],
                "coherence_score": row[4],
                "fluency_score": row[5],
                "detailed_results": json.loads(row[6]) if row[6] else None
            })
        
        conn.close()
        return results 