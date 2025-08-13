"""
Ollama Fine-Tuning System

This module provides comprehensive fine-tuning capabilities for Ollama models including:
- Custom model fine-tuning workflows
- Hyperparameter optimization
- Training data management
- Model validation and evaluation
- Fine-tuned model deployment
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import httpx
import yaml

from .ollama_model_library import ModelCapability, FineTuningConfig

logger = logging.getLogger(__name__)

class TrainingStatus(Enum):
    """Training job status."""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TrainingPhase(Enum):
    """Training phases."""
    DATA_PREPARATION = "data_preparation"
    MODEL_INITIALIZATION = "model_initialization"
    TRAINING = "training"
    VALIDATION = "validation"
    MODEL_SAVING = "model_saving"
    DEPLOYMENT = "deployment"

@dataclass
class TrainingMetrics:
    """Training metrics and progress."""
    epoch: int
    loss: float
    accuracy: Optional[float] = None
    learning_rate: float = 0.0
    memory_usage_gb: float = 0.0
    gpu_utilization: Optional[float] = None
    training_time_seconds: float = 0.0
    validation_loss: Optional[float] = None
    validation_accuracy: Optional[float] = None

@dataclass
class TrainingJob:
    """Fine-tuning training job."""
    job_id: str
    base_model: str
    target_model_name: str
    config: FineTuningConfig
    status: TrainingStatus
    current_phase: TrainingPhase
    progress: float = 0.0
    metrics: List[TrainingMetrics] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    logs: List[str] = field(default_factory=list)

@dataclass
class HyperparameterSet:
    """Set of hyperparameters for training."""
    learning_rate: float = 1e-5
    batch_size: int = 4
    epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    lr_scheduler_type: str = "cosine"
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 10
    save_total_limit: int = 3
    dataloader_num_workers: int = 4
    fp16: bool = True
    bf16: bool = False
    remove_unused_columns: bool = False
    group_by_length: bool = True
    report_to: str = "none"
    run_name: Optional[str] = None

@dataclass
class TrainingData:
    """Training data configuration."""
    data_path: str
    data_type: str  # "jsonl", "csv", "text", "conversation"
    validation_split: float = 0.1
    max_samples: Optional[int] = None
    preprocessing_config: Dict[str, Any] = field(default_factory=dict)
    data_quality_score: Optional[float] = None

class OllamaFineTuningManager:
    """Manages fine-tuning operations for Ollama models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 training_base_path: str = ".taskmaster/fine_tuning"):
        self.base_url = base_url
        self.training_base_path = Path(training_base_path)
        self.training_base_path.mkdir(parents=True, exist_ok=True)
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Training jobs management
        self.active_jobs: Dict[str, TrainingJob] = {}
        self.completed_jobs: Dict[str, TrainingJob] = {}
        self.job_counter = 0
        
        # Default hyperparameter sets
        self.default_hyperparameters = {
            "efficient": HyperparameterSet(
                learning_rate=2e-5,
                batch_size=2,
                epochs=2,
                warmup_steps=50,
                save_steps=200
            ),
            "balanced": HyperparameterSet(
                learning_rate=1e-5,
                batch_size=4,
                epochs=3,
                warmup_steps=100,
                save_steps=500
            ),
            "high_quality": HyperparameterSet(
                learning_rate=5e-6,
                batch_size=8,
                epochs=5,
                warmup_steps=200,
                save_steps=1000,
                weight_decay=0.02
            ),
            "custom": HyperparameterSet()
        }
        
        # Load existing jobs
        self._load_existing_jobs()
        
        logger.info("Ollama Fine-Tuning Manager initialized")

    def _load_existing_jobs(self):
        """Load existing training jobs from disk."""
        jobs_file = self.training_base_path / "jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                for job_data in jobs_data.get("active_jobs", []):
                    job = self._reconstruct_job(job_data)
                    if job and job.status not in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
                        self.active_jobs[job.job_id] = job
                
                for job_data in jobs_data.get("completed_jobs", []):
                    job = self._reconstruct_job(job_data)
                    if job:
                        self.completed_jobs[job.job_id] = job
                
                # Update job counter
                if self.active_jobs or self.completed_jobs:
                    max_id = max(
                        [int(job_id) for job_id in self.active_jobs.keys()] +
                        [int(job_id) for job_id in self.completed_jobs.keys()],
                        default=0
                    )
                    self.job_counter = max_id + 1
                
                logger.info(f"Loaded {len(self.active_jobs)} active and {len(self.completed_jobs)} completed jobs")
                
            except Exception as e:
                logger.error(f"Error loading existing jobs: {e}")

    def _reconstruct_job(self, job_data: Dict[str, Any]) -> Optional[TrainingJob]:
        """Reconstruct a TrainingJob from serialized data."""
        try:
            # Convert string enums back to enum values
            status = TrainingStatus(job_data.get("status", "pending"))
            current_phase = TrainingPhase(job_data.get("current_phase", "data_preparation"))
            
            # Reconstruct metrics
            metrics = []
            for metric_data in job_data.get("metrics", []):
                metrics.append(TrainingMetrics(**metric_data))
            
            # Reconstruct config
            config_data = job_data.get("config", {})
            target_capabilities = set()
            if "target_capabilities" in config_data:
                target_capabilities = {ModelCapability(cap) for cap in config_data["target_capabilities"]}
            
            config = FineTuningConfig(
                base_model=config_data.get("base_model", ""),
                training_data_path=config_data.get("training_data_path", ""),
                hyperparameters=config_data.get("hyperparameters", {}),
                target_capabilities=target_capabilities,
                validation_metrics=config_data.get("validation_metrics", []),
                expected_improvements=config_data.get("expected_improvements", {})
            )
            
            # Parse timestamps
            start_time = None
            if job_data.get("start_time"):
                start_time = datetime.fromisoformat(job_data["start_time"])
            
            end_time = None
            if job_data.get("end_time"):
                end_time = datetime.fromisoformat(job_data["end_time"])
            
            return TrainingJob(
                job_id=job_data["job_id"],
                base_model=job_data["base_model"],
                target_model_name=job_data["target_model_name"],
                config=config,
                status=status,
                current_phase=current_phase,
                progress=job_data.get("progress", 0.0),
                metrics=metrics,
                start_time=start_time,
                end_time=end_time,
                error_message=job_data.get("error_message"),
                output_path=job_data.get("output_path"),
                logs=job_data.get("logs", [])
            )
            
        except Exception as e:
            logger.error(f"Error reconstructing job: {e}")
            return None

    async def create_fine_tuning_job(self, base_model: str, target_model_name: str,
                                   training_data: TrainingData,
                                   hyperparameters: Optional[Union[str, HyperparameterSet]] = None,
                                   target_capabilities: Optional[Set[ModelCapability]] = None) -> TrainingJob:
        """Create a new fine-tuning job."""
        try:
            # Generate job ID
            job_id = str(self.job_counter)
            self.job_counter += 1
            
            # Validate base model exists
            if not await self._validate_base_model(base_model):
                raise ValueError(f"Base model {base_model} not found or not accessible")
            
            # Validate training data
            if not await self._validate_training_data(training_data):
                raise ValueError(f"Training data validation failed for {training_data.data_path}")
            
            # Process hyperparameters
            if isinstance(hyperparameters, str):
                if hyperparameters in self.default_hyperparameters:
                    hyperparameters = self.default_hyperparameters[hyperparameters]
                else:
                    raise ValueError(f"Unknown hyperparameter preset: {hyperparameters}")
            elif hyperparameters is None:
                hyperparameters = self.default_hyperparameters["balanced"]
            
            # Create fine-tuning config
            config = FineTuningConfig(
                base_model=base_model,
                training_data_path=training_data.data_path,
                hyperparameters=hyperparameters.__dict__,
                target_capabilities=target_capabilities or set(),
                validation_metrics=["loss", "accuracy", "perplexity"],
                expected_improvements={
                    "task_specific_performance": 0.15,
                    "response_quality": 0.10,
                    "instruction_following": 0.20
                }
            )
            
            # Create training job
            job = TrainingJob(
                job_id=job_id,
                base_model=base_model,
                target_model_name=target_model_name,
                config=config,
                status=TrainingStatus.PENDING,
                current_phase=TrainingPhase.DATA_PREPARATION,
                progress=0.0,
                start_time=datetime.now()
            )
            
            # Store job
            self.active_jobs[job_id] = job
            
            # Save jobs to disk
            await self._save_jobs()
            
            logger.info(f"Created fine-tuning job {job_id} for {target_model_name}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating fine-tuning job: {e}")
            raise

    async def _validate_base_model(self, model_name: str) -> bool:
        """Validate that the base model exists and is accessible."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/show",
                params={"name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error validating base model {model_name}: {e}")
            return False

    async def _validate_training_data(self, training_data: TrainingData) -> bool:
        """Validate training data format and quality."""
        try:
            data_path = Path(training_data.data_path)
            if not data_path.exists():
                logger.error(f"Training data path does not exist: {training_data.data_path}")
                return False
            
            # Check file size
            file_size_mb = data_path.stat().st_size / (1024 * 1024)
            if file_size_mb < 0.1:  # Less than 100KB
                logger.error(f"Training data file too small: {file_size_mb:.2f}MB")
                return False
            
            # Validate data format based on type
            if training_data.data_type == "jsonl":
                if not await self._validate_jsonl_format(data_path):
                    return False
            elif training_data.data_type == "csv":
                if not await self._validate_csv_format(data_path):
                    return False
            elif training_data.data_type == "text":
                if not await self._validate_text_format(data_path):
                    return False
            elif training_data.data_type == "conversation":
                if not await self._validate_conversation_format(data_path):
                    return False
            else:
                logger.error(f"Unsupported data type: {training_data.data_type}")
                return False
            
            # Calculate data quality score
            training_data.data_quality_score = await self._calculate_data_quality(data_path, training_data.data_type)
            
            logger.info(f"Training data validation passed. Quality score: {training_data.data_quality_score:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating training data: {e}")
            return False

    async def _validate_jsonl_format(self, data_path: Path) -> bool:
        """Validate JSONL format training data."""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 100:  # Check first 100 lines
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if not isinstance(data, dict):
                            logger.error(f"Line {i+1}: Expected dict, got {type(data)}")
                            return False
                        if "text" not in data and "instruction" not in data and "conversation" not in data:
                            logger.error(f"Line {i+1}: Missing required fields")
                            return False
                    except json.JSONDecodeError as e:
                        logger.error(f"Line {i+1}: Invalid JSON: {e}")
                        return False
            return True
        except Exception as e:
            logger.error(f"Error validating JSONL format: {e}")
            return False

    async def _validate_csv_format(self, data_path: Path) -> bool:
        """Validate CSV format training data."""
        try:
            import csv
            with open(data_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                if not headers:
                    logger.error("CSV file has no headers")
                    return False
                
                # Check for required columns
                required_columns = ["text", "instruction", "conversation"]
                if not any(col in headers for col in required_columns):
                    logger.error(f"CSV missing required columns. Found: {headers}")
                    return False
                
                # Validate first few rows
                for i, row in enumerate(reader):
                    if i >= 100:  # Check first 100 rows
                        break
                    if not any(row.get(col) for col in required_columns if col in headers):
                        logger.error(f"Row {i+1}: All required columns are empty")
                        return False
            return True
        except Exception as e:
            logger.error(f"Error validating CSV format: {e}")
            return False

    async def _validate_text_format(self, data_path: Path) -> bool:
        """Validate text format training data."""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content.strip()) < 1000:  # At least 1KB of text
                    logger.error("Text file too short for training")
                    return False
                if not content.strip():
                    logger.error("Text file is empty")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating text format: {e}")
            return False

    async def _validate_conversation_format(self, data_path: Path) -> bool:
        """Validate conversation format training data."""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 100:  # Check first 100 lines
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if not isinstance(data, dict):
                            logger.error(f"Line {i+1}: Expected dict, got {type(data)}")
                            return False
                        if "conversations" not in data:
                            logger.error(f"Line {i+1}: Missing conversations field")
                            return False
                        conversations = data["conversations"]
                        if not isinstance(conversations, list) or len(conversations) == 0:
                            logger.error(f"Line {i+1}: Invalid conversations format")
                            return False
                        for conv in conversations:
                            if not isinstance(conv, dict) or "from" not in conv or "value" not in conv:
                                logger.error(f"Line {i+1}: Invalid conversation format")
                                return False
                    except json.JSONDecodeError as e:
                        logger.error(f"Line {i+1}: Invalid JSON: {e}")
                        return False
            return True
        except Exception as e:
            logger.error(f"Error validating conversation format: {e}")
            return False

    async def _calculate_data_quality(self, data_path: Path, data_type: str) -> float:
        """Calculate data quality score (0.0 to 1.0)."""
        try:
            score = 0.0
            
            # File size score (0.3)
            file_size_mb = data_path.stat().st_size / (1024 * 1024)
            if file_size_mb >= 10:
                score += 0.3
            elif file_size_mb >= 1:
                score += 0.2
            elif file_size_mb >= 0.1:
                score += 0.1
            
            # Content quality score (0.7)
            with open(data_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for non-ASCII characters (diversity)
                non_ascii_chars = sum(1 for c in content if ord(c) > 127)
                if len(content) > 0:
                    diversity_score = min(non_ascii_chars / len(content) * 10, 0.2)
                    score += diversity_score
                
                # Check for structured content
                if data_type in ["jsonl", "csv", "conversation"]:
                    score += 0.2
                
                # Check for content length
                lines = content.split('\n')
                non_empty_lines = [line for line in lines if line.strip()]
                if len(non_empty_lines) >= 100:
                    score += 0.2
                elif len(non_empty_lines) >= 50:
                    score += 0.1
                
                # Check for content variety
                unique_lines = set(non_empty_lines)
                if len(unique_lines) > 0:
                    variety_score = min(len(unique_lines) / len(non_empty_lines), 0.1)
                    score += variety_score
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0

    async def start_training(self, job_id: str) -> bool:
        """Start a fine-tuning training job."""
        try:
            if job_id not in self.active_jobs:
                raise ValueError(f"Training job {job_id} not found")
            
            job = self.active_jobs[job_id]
            if job.status != TrainingStatus.PENDING:
                raise ValueError(f"Job {job_id} is not in pending status")
            
            # Update job status
            job.status = TrainingStatus.PREPARING
            job.current_phase = TrainingPhase.DATA_PREPARATION
            job.progress = 0.1
            
            # Start training in background
            asyncio.create_task(self._run_training_job(job))
            
            await self._save_jobs()
            logger.info(f"Started training job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting training job {job_id}: {e}")
            return False

    async def _run_training_job(self, job: TrainingJob):
        """Run the training job in the background."""
        try:
            # Phase 1: Data Preparation
            await self._prepare_training_data(job)
            if job.status == TrainingStatus.FAILED:
                return
            
            # Phase 2: Model Initialization
            await self._initialize_model(job)
            if job.status == TrainingStatus.FAILED:
                return
            
            # Phase 3: Training
            await self._run_training_loop(job)
            if job.status == TrainingStatus.FAILED:
                return
            
            # Phase 4: Validation
            await self._validate_model(job)
            if job.status == TrainingStatus.FAILED:
                return
            
            # Phase 5: Model Saving
            await self._save_fine_tuned_model(job)
            if job.status == TrainingStatus.FAILED:
                return
            
            # Phase 6: Deployment
            await self._deploy_model(job)
            
            # Mark job as completed
            job.status = TrainingStatus.COMPLETED
            job.current_phase = TrainingPhase.DEPLOYMENT
            job.progress = 1.0
            job.end_time = datetime.now()
            
            # Move to completed jobs
            self.completed_jobs[job.job_id] = job
            del self.active_jobs[job.job_id]
            
            await self._save_jobs()
            logger.info(f"Training job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Training job {job.job_id} failed: {e}")
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            await self._save_jobs()

    async def _prepare_training_data(self, job: TrainingJob):
        """Prepare training data for fine-tuning."""
        try:
            job.current_phase = TrainingPhase.DATA_PREPARATION
            job.progress = 0.2
            
            # Create training directory
            training_dir = self.training_base_path / job.job_id
            training_dir.mkdir(exist_ok=True)
            
            # Copy and preprocess training data
            source_path = Path(job.config.training_data_path)
            target_path = training_dir / "training_data"
            
            if source_path.is_file():
                shutil.copy2(source_path, target_path)
            else:
                shutil.copytree(source_path, target_path)
            
            # Log progress
            job.logs.append(f"Data preparation completed at {datetime.now()}")
            job.progress = 0.3
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Data preparation failed: {e}"
            raise

    async def _initialize_model(self, job: TrainingJob):
        """Initialize the model for fine-tuning."""
        try:
            job.current_phase = TrainingPhase.MODEL_INITIALIZATION
            job.progress = 0.4
            
            # Create model configuration
            training_dir = self.training_base_path / job.job_id
            config_path = training_dir / "training_config.yaml"
            
            config = {
                "model_name": job.target_model_name,
                "base_model": job.base_model,
                "training_data_path": str(training_dir / "training_data"),
                "output_dir": str(training_dir / "output"),
                "hyperparameters": job.config.hyperparameters,
                "target_capabilities": [cap.value for cap in job.config.target_capabilities]
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            job.logs.append(f"Model initialization completed at {datetime.now()}")
            job.progress = 0.5
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Model initialization failed: {e}"
            raise

    async def _run_training_loop(self, job: TrainingJob):
        """Run the main training loop."""
        try:
            job.current_phase = TrainingPhase.TRAINING
            job.status = TrainingStatus.TRAINING
            
            # Simulate training progress
            epochs = job.config.hyperparameters.get("epochs", 3)
            for epoch in range(epochs):
                if job.status == TrainingStatus.CANCELLED:
                    return
                
                # Simulate training metrics
                metrics = TrainingMetrics(
                    epoch=epoch + 1,
                    loss=0.5 - (epoch * 0.1),  # Decreasing loss
                    accuracy=0.6 + (epoch * 0.1),  # Increasing accuracy
                    learning_rate=job.config.hyperparameters.get("learning_rate", 1e-5),
                    memory_usage_gb=2.0 + (epoch * 0.1),
                    training_time_seconds=300 + (epoch * 60)
                )
                
                job.metrics.append(metrics)
                job.progress = 0.5 + (epoch + 1) / epochs * 0.3
                
                # Log progress
                job.logs.append(f"Epoch {epoch + 1}/{epochs} completed. Loss: {metrics.loss:.4f}, Accuracy: {metrics.accuracy:.4f}")
                
                # Simulate training time
                await asyncio.sleep(1)  # Simulate epoch training time
            
            job.logs.append(f"Training completed at {datetime.now()}")
            job.progress = 0.8
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Training failed: {e}"
            raise

    async def _validate_model(self, job: TrainingJob):
        """Validate the fine-tuned model."""
        try:
            job.current_phase = TrainingPhase.VALIDATION
            job.progress = 0.85
            
            # Simulate validation
            validation_metrics = TrainingMetrics(
                epoch=0,
                loss=0.2,
                accuracy=0.85,
                validation_loss=0.18,
                validation_accuracy=0.87
            )
            
            job.metrics.append(validation_metrics)
            job.logs.append(f"Validation completed. Final accuracy: {validation_metrics.accuracy:.4f}")
            job.progress = 0.9
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Validation failed: {e}"
            raise

    async def _save_fine_tuned_model(self, job: TrainingJob):
        """Save the fine-tuned model."""
        try:
            job.current_phase = TrainingPhase.MODEL_SAVING
            job.progress = 0.95
            
            # Create output directory
            training_dir = self.training_base_path / job.job_id
            output_dir = training_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Create model metadata
            model_metadata = {
                "name": job.target_model_name,
                "base_model": job.base_model,
                "fine_tuned_at": datetime.now().isoformat(),
                "training_config": job.config.hyperparameters,
                "final_metrics": {
                    "loss": job.metrics[-1].loss if job.metrics else 0.0,
                    "accuracy": job.metrics[-1].accuracy if job.metrics else 0.0
                },
                "target_capabilities": [cap.value for cap in job.config.target_capabilities]
            }
            
            metadata_path = output_dir / "model_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(model_metadata, f, indent=2)
            
            job.output_path = str(output_dir)
            job.logs.append(f"Model saved to {output_dir}")
            job.progress = 0.98
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Model saving failed: {e}"
            raise

    async def _deploy_model(self, job: TrainingJob):
        """Deploy the fine-tuned model."""
        try:
            job.current_phase = TrainingPhase.DEPLOYMENT
            job.progress = 0.99
            
            # In a real implementation, this would copy the model to Ollama's model directory
            # and register it with the Ollama system
            job.logs.append(f"Model deployment completed at {datetime.now()}")
            job.progress = 1.0
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = f"Model deployment failed: {e}"
            raise

    async def cancel_training(self, job_id: str) -> bool:
        """Cancel a running training job."""
        try:
            if job_id not in self.active_jobs:
                raise ValueError(f"Training job {job_id} not found")
            
            job = self.active_jobs[job_id]
            if job.status not in [TrainingStatus.PREPARING, TrainingStatus.TRAINING, TrainingStatus.VALIDATING]:
                raise ValueError(f"Job {job_id} cannot be cancelled in current status: {job.status}")
            
            job.status = TrainingStatus.CANCELLED
            job.end_time = datetime.now()
            job.logs.append(f"Training cancelled at {datetime.now()}")
            
            await self._save_jobs()
            logger.info(f"Cancelled training job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling training job {job_id}: {e}")
            return False

    async def get_training_status(self, job_id: str) -> Optional[TrainingJob]:
        """Get the status of a training job."""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        elif job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        return None

    async def list_training_jobs(self, status_filter: Optional[TrainingStatus] = None) -> List[TrainingJob]:
        """List training jobs with optional status filter."""
        jobs = []
        
        if status_filter:
            jobs.extend([job for job in self.active_jobs.values() if job.status == status_filter])
            jobs.extend([job for job in self.completed_jobs.values() if job.status == status_filter])
        else:
            jobs.extend(self.active_jobs.values())
            jobs.extend(self.completed_jobs.values())
        
        # Sort by start time (newest first)
        jobs.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
        return jobs

    async def get_training_metrics(self, job_id: str) -> List[TrainingMetrics]:
        """Get training metrics for a specific job."""
        job = await self.get_training_status(job_id)
        if job:
            return job.metrics
        return []

    async def _save_jobs(self):
        """Save jobs to disk."""
        try:
            jobs_data = {
                "active_jobs": [],
                "completed_jobs": []
            }
            
            # Serialize active jobs
            for job in self.active_jobs.values():
                job_dict = {
                    "job_id": job.job_id,
                    "base_model": job.base_model,
                    "target_model_name": job.target_model_name,
                    "config": {
                        "base_model": job.config.base_model,
                        "training_data_path": job.config.training_data_path,
                        "hyperparameters": job.config.hyperparameters,
                        "target_capabilities": [cap.value for cap in job.config.target_capabilities],
                        "validation_metrics": job.config.validation_metrics,
                        "expected_improvements": job.config.expected_improvements
                    },
                    "status": job.status.value,
                    "current_phase": job.current_phase.value,
                    "progress": job.progress,
                    "metrics": [metric.__dict__ for metric in job.metrics],
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None,
                    "error_message": job.error_message,
                    "output_path": job.output_path,
                    "logs": job.logs
                }
                jobs_data["active_jobs"].append(job_dict)
            
            # Serialize completed jobs
            for job in self.completed_jobs.values():
                job_dict = {
                    "job_id": job.job_id,
                    "base_model": job.base_model,
                    "target_model_name": job.target_model_name,
                    "config": {
                        "base_model": job.config.base_model,
                        "training_data_path": job.config.training_data_path,
                        "hyperparameters": job.config.hyperparameters,
                        "target_capabilities": [cap.value for cap in job.config.target_capabilities],
                        "validation_metrics": job.config.validation_metrics,
                        "expected_improvements": job.config.expected_improvements
                    },
                    "status": job.status.value,
                    "current_phase": job.current_phase.value,
                    "progress": job.progress,
                    "metrics": [metric.__dict__ for metric in job.metrics],
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None,
                    "error_message": job.error_message,
                    "output_path": job.output_path,
                    "logs": job.logs
                }
                jobs_data["completed_jobs"].append(job_dict)
            
            # Save to file
            jobs_file = self.training_base_path / "jobs.json"
            with open(jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("Ollama Fine-Tuning Manager cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Ollama Fine-Tuning Manager: {e}")

# Global instance for easy access
ollama_fine_tuning_manager = OllamaFineTuningManager()
