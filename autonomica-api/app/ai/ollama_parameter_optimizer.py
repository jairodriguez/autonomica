"""
Ollama Parameter Optimization System

This module provides comprehensive parameter optimization for Ollama models including:
- Automatic hyperparameter tuning
- Performance optimization
- Model configuration optimization
- Resource utilization optimization
- Quality vs. speed trade-off optimization
"""

import asyncio
import json
import logging
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx
import numpy as np

logger = logging.getLogger(__name__)

class OptimizationObjective(Enum):
    """Optimization objectives."""
    MAXIMIZE_QUALITY = "maximize_quality"
    MINIMIZE_LATENCY = "minimize_latency"
    MINIMIZE_MEMORY = "minimize_memory"
    BALANCE_QUALITY_SPEED = "balance_quality_speed"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    CUSTOM = "custom"

class OptimizationStrategy(Enum):
    """Optimization strategies."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    EVOLUTIONARY = "evolutionary"
    HYPERBAND = "hyperband"

@dataclass
class ParameterRange:
    """Range for a parameter during optimization."""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Optional[Union[int, float]] = None
    log_scale: bool = False
    discrete_values: Optional[List[Union[int, float, str]]] = None

@dataclass
class OptimizationConfig:
    """Configuration for parameter optimization."""
    objective: OptimizationObjective
    strategy: OptimizationStrategy
    max_iterations: int = 100
    max_time_minutes: int = 60
    evaluation_budget: int = 50
    parallel_evaluations: int = 1
    early_stopping_patience: int = 10
    min_improvement: float = 0.01
    custom_objective_function: Optional[Callable] = None
    parameter_ranges: Dict[str, ParameterRange] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParameterSet:
    """A set of parameters to evaluate."""
    parameters: Dict[str, Any]
    evaluation_id: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    """Result of a parameter evaluation."""
    evaluation_id: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    quality_score: float
    latency_ms: float
    memory_usage_gb: float
    throughput_tokens_per_sec: float
    resource_efficiency: float
    overall_score: float
    evaluation_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationSession:
    """An optimization session."""
    session_id: str
    model_name: str
    config: OptimizationConfig
    status: str = "running"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    best_result: Optional[OptimizationResult] = None
    all_results: List[OptimizationResult] = field(default_factory=list)
    current_iteration: int = 0
    convergence_history: List[float] = field(default_factory=list)

class OllamaParameterOptimizer:
    """Optimizes Ollama model parameters for various objectives."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Optimization sessions
        self.active_sessions: Dict[str, OptimizationSession] = {}
        self.completed_sessions: Dict[str, OptimizationSession] = {}
        self.session_counter = 0
        
        # Default parameter ranges for common models
        self.default_parameter_ranges = self._initialize_default_ranges()
        
        # Optimization history
        self.optimization_history: List[OptimizationResult] = []
        
        logger.info("Ollama Parameter Optimizer initialized")

    def _initialize_default_ranges(self) -> Dict[str, Dict[str, ParameterRange]]:
        """Initialize default parameter ranges for different model types."""
        return {
            "general": {
                "temperature": ParameterRange("temperature", 0.1, 1.0, 0.1),
                "top_p": ParameterRange("top_p", 0.1, 1.0, 0.1),
                "top_k": ParameterRange("top_k", 1, 100, 1),
                "repeat_penalty": ParameterRange("repeat_penalty", 1.0, 2.0, 0.1),
                "num_ctx": ParameterRange("num_ctx", 512, 8192, 512),
                "num_thread": ParameterRange("num_thread", 1, 16, 1),
                "num_gpu": ParameterRange("num_gpu", 0, 4, 1),
                "seed": ParameterRange("seed", 1, 1000000, 1)
            },
            "code": {
                "temperature": ParameterRange("temperature", 0.1, 0.8, 0.1),
                "top_p": ParameterRange("top_p", 0.1, 0.9, 0.1),
                "top_k": ParameterRange("top_k", 1, 50, 1),
                "repeat_penalty": ParameterRange("repeat_penalty", 1.0, 1.5, 0.1),
                "num_ctx": ParameterRange("num_ctx", 1024, 16384, 1024),
                "num_thread": ParameterRange("num_thread", 2, 16, 2),
                "num_gpu": ParameterRange("num_gpu", 0, 4, 1),
                "seed": ParameterRange("seed", 1, 1000000, 1)
            },
            "creative": {
                "temperature": ParameterRange("temperature", 0.7, 1.2, 0.1),
                "top_p": ParameterRange("top_p", 0.8, 1.0, 0.05),
                "top_k": ParameterRange("top_k", 10, 100, 5),
                "repeat_penalty": ParameterRange("repeat_penalty", 1.0, 1.8, 0.1),
                "num_ctx": ParameterRange("num_ctx", 1024, 8192, 1024),
                "num_thread": ParameterRange("num_thread", 1, 16, 1),
                "num_gpu": ParameterRange("num_gpu", 0, 4, 1),
                "seed": ParameterRange("seed", 1, 1000000, 1)
            },
            "analysis": {
                "temperature": ParameterRange("temperature", 0.1, 0.5, 0.1),
                "top_p": ParameterRange("top_p", 0.1, 0.7, 0.1),
                "top_k": ParameterRange("top_k", 1, 30, 1),
                "repeat_penalty": ParameterRange("repeat_penalty", 1.0, 1.3, 0.1),
                "num_ctx": ParameterRange("num_ctx", 2048, 16384, 1024),
                "num_thread": ParameterRange("num_thread", 2, 16, 2),
                "num_gpu": ParameterRange("num_gpu", 0, 4, 1),
                "seed": ParameterRange("seed", 1, 1000000, 1)
            }
        }

    async def create_optimization_session(self, model_name: str, 
                                        objective: OptimizationObjective,
                                        strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN_OPTIMIZATION,
                                        model_type: str = "general",
                                        custom_config: Optional[OptimizationConfig] = None) -> OptimizationSession:
        """Create a new parameter optimization session."""
        try:
            # Generate session ID
            session_id = str(self.session_counter)
            self.session_counter += 1
            
            # Validate model exists
            if not await self._validate_model(model_name):
                raise ValueError(f"Model {model_name} not found or not accessible")
            
            # Create optimization configuration
            if custom_config:
                config = custom_config
            else:
                config = OptimizationConfig(
                    objective=objective,
                    strategy=strategy,
                    parameter_ranges=self.default_parameter_ranges.get(model_type, self.default_parameter_ranges["general"])
                )
            
            # Create optimization session
            session = OptimizationSession(
                session_id=session_id,
                model_name=model_name,
                config=config
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            logger.info(f"Created optimization session {session_id} for {model_name}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating optimization session: {e}")
            raise

    async def _validate_model(self, model_name: str) -> bool:
        """Validate that the model exists and is accessible."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/show",
                params={"name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error validating model {model_name}: {e}")
            return False

    async def start_optimization(self, session_id: str) -> bool:
        """Start parameter optimization for a session."""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Optimization session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Start optimization in background
            asyncio.create_task(self._run_optimization(session))
            
            logger.info(f"Started optimization session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting optimization session {session_id}: {e}")
            return False

    async def _run_optimization(self, session: OptimizationSession):
        """Run the optimization process."""
        try:
            start_time = datetime.now()
            
            if session.config.strategy == OptimizationStrategy.GRID_SEARCH:
                await self._run_grid_search(session)
            elif session.config.strategy == OptimizationStrategy.RANDOM_SEARCH:
                await self._run_random_search(session)
            elif session.config.strategy == OptimizationStrategy.BAYESIAN_OPTIMIZATION:
                await self._run_bayesian_optimization(session)
            elif session.config.strategy == OptimizationStrategy.EVOLUTIONARY:
                await self._run_evolutionary_optimization(session)
            elif session.config.strategy == OptimizationStrategy.HYPERBAND:
                await self._run_hyperband_optimization(session)
            else:
                raise ValueError(f"Unknown optimization strategy: {session.config.strategy}")
            
            # Mark session as completed
            session.status = "completed"
            session.end_time = datetime.now()
            
            # Move to completed sessions
            self.completed_sessions[session.session_id] = session
            del self.active_sessions[session.session_id]
            
            logger.info(f"Optimization session {session.session_id} completed")
            
        except Exception as e:
            logger.error(f"Optimization session {session.session_id} failed: {e}")
            session.status = "failed"
            session.end_time = datetime.now()

    async def _run_grid_search(self, session: OptimizationSession):
        """Run grid search optimization."""
        try:
            # Generate parameter combinations
            param_combinations = self._generate_grid_combinations(session.config.parameter_ranges)
            
            # Limit to max iterations
            if len(param_combinations) > session.config.max_iterations:
                param_combinations = random.sample(param_combinations, session.config.max_iterations)
            
            # Evaluate each combination
            for i, params in enumerate(param_combinations):
                if session.current_iteration >= session.config.max_iterations:
                    break
                
                # Create parameter set
                param_set = ParameterSet(
                    parameters=params,
                    evaluation_id=f"{session.session_id}_{i}"
                )
                
                # Evaluate parameters
                result = await self._evaluate_parameters(session.model_name, param_set)
                if result:
                    session.all_results.append(result)
                    session.current_iteration += 1
                    
                    # Update best result
                    if (session.best_result is None or 
                        result.overall_score > session.best_result.overall_score):
                        session.best_result = result
                        session.convergence_history.append(result.overall_score)
                    
                    # Check early stopping
                    if self._should_stop_early(session):
                        break
                
                # Add delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Grid search optimization failed: {e}")
            raise

    async def _run_random_search(self, session: OptimizationSession):
        """Run random search optimization."""
        try:
            for i in range(session.config.max_iterations):
                if session.current_iteration >= session.config.max_iterations:
                    break
                
                # Generate random parameters
                params = self._generate_random_parameters(session.config.parameter_ranges)
                
                # Create parameter set
                param_set = ParameterSet(
                    parameters=params,
                    evaluation_id=f"{session.session_id}_{i}"
                )
                
                # Evaluate parameters
                result = await self._evaluate_parameters(session.model_name, param_set)
                if result:
                    session.all_results.append(result)
                    session.current_iteration += 1
                    
                    # Update best result
                    if (session.best_result is None or 
                        result.overall_score > session.best_result.overall_score):
                        session.best_result = result
                        session.convergence_history.append(result.overall_score)
                    
                    # Check early stopping
                    if self._should_stop_early(session):
                        break
                
                # Add delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Random search optimization failed: {e}")
            raise

    async def _run_bayesian_optimization(self, session: OptimizationSession):
        """Run Bayesian optimization."""
        try:
            # Initialize with random samples
            n_initial = min(10, session.config.max_iterations // 4)
            initial_params = []
            
            for i in range(n_initial):
                params = self._generate_random_parameters(session.config.parameter_ranges)
                initial_params.append(params)
                
                # Evaluate initial parameters
                param_set = ParameterSet(
                    parameters=params,
                    evaluation_id=f"{session.session_id}_init_{i}"
                )
                
                result = await self._evaluate_parameters(session.model_name, param_set)
                if result:
                    session.all_results.append(result)
                    session.current_iteration += 1
                    
                    if (session.best_result is None or 
                        result.overall_score > session.best_result.overall_score):
                        session.best_result = result
                        session.convergence_history.append(result.overall_score)
                
                await asyncio.sleep(0.1)
            
            # Bayesian optimization loop
            for i in range(n_initial, session.config.max_iterations):
                if session.current_iteration >= session.config.max_iterations:
                    break
                
                # Generate next parameters using acquisition function
                next_params = self._generate_bayesian_parameters(session)
                
                # Create parameter set
                param_set = ParameterSet(
                    parameters=next_params,
                    evaluation_id=f"{session.session_id}_bayes_{i}"
                )
                
                # Evaluate parameters
                result = await self._evaluate_parameters(session.model_name, param_set)
                if result:
                    session.all_results.append(result)
                    session.current_iteration += 1
                    
                    # Update best result
                    if (session.best_result is None or 
                        result.overall_score > session.best_result.overall_score):
                        session.best_result = result
                        session.convergence_history.append(result.overall_score)
                    
                    # Check early stopping
                    if self._should_stop_early(session):
                        break
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Bayesian optimization failed: {e}")
            raise

    async def _run_evolutionary_optimization(self, session: OptimizationSession):
        """Run evolutionary optimization."""
        try:
            # Initialize population
            population_size = min(20, session.config.max_iterations // 5)
            population = []
            
            for i in range(population_size):
                params = self._generate_random_parameters(session.config.parameter_ranges)
                population.append(params)
                
                # Evaluate initial parameters
                param_set = ParameterSet(
                    parameters=params,
                    evaluation_id=f"{session.session_id}_init_{i}"
                )
                
                result = await self._evaluate_parameters(session.model_name, param_set)
                if result:
                    session.all_results.append(result)
                    session.current_iteration += 1
                    
                    if (session.best_result is None or 
                        result.overall_score > session.best_result.overall_score):
                        session.best_result = result
                        session.convergence_history.append(result.overall_score)
                
                await asyncio.sleep(0.1)
            
            # Evolutionary loop
            generations = (session.config.max_iterations - population_size) // population_size
            
            for generation in range(generations):
                if session.current_iteration >= session.config.max_iterations:
                    break
                
                # Select parents
                parents = self._select_parents(session.all_results, population_size // 2)
                
                # Generate offspring
                offspring = []
                for _ in range(population_size):
                    if len(parents) >= 2:
                        child = self._crossover(parents[0], parents[1])
                        child = self._mutate(child, session.config.parameter_ranges)
                        offspring.append(child)
                    else:
                        child = self._generate_random_parameters(session.config.parameter_ranges)
                        offspring.append(child)
                
                # Evaluate offspring
                for i, params in enumerate(offspring):
                    param_set = ParameterSet(
                        parameters=params,
                        evaluation_id=f"{session.session_id}_gen_{generation}_{i}"
                    )
                    
                    result = await self._evaluate_parameters(session.model_name, param_set)
                    if result:
                        session.all_results.append(result)
                        session.current_iteration += 1
                        
                        # Update best result
                        if (session.best_result is None or 
                            result.overall_score > session.best_result.overall_score):
                            session.best_result = result
                            session.convergence_history.append(result.overall_score)
                        
                        # Check early stopping
                        if self._should_stop_early(session):
                            break
                    
                    await asyncio.sleep(0.1)
                
                if self._should_stop_early(session):
                    break
                
        except Exception as e:
            logger.error(f"Evolutionary optimization failed: {e}")
            raise

    async def _run_hyperband_optimization(self, session: OptimizationSession):
        """Run Hyperband optimization."""
        try:
            # Hyperband configuration
            R = 81  # Maximum resource allocation
            eta = 3  # Successive halving parameter
            
            # Calculate number of brackets
            s_max = int(math.log(R, eta))
            B = (s_max + 1) * R
            
            for s in range(s_max, -1, -1):
                n = int(math.ceil(B / R / eta ** s))
                r = R * eta ** s
                
                # Sample n configurations
                configs = []
                for i in range(n):
                    params = self._generate_random_parameters(session.config.parameter_ranges)
                    configs.append(params)
                
                # Successive halving
                for i in range(s + 1):
                    n_i = int(n * eta ** (-i))
                    r_i = int(r * eta ** i)
                    
                    # Evaluate configurations with resource allocation r_i
                    for j, params in enumerate(configs[:n_i]):
                        if session.current_iteration >= session.config.max_iterations:
                            break
                        
                        param_set = ParameterSet(
                            parameters=params,
                            evaluation_id=f"{session.session_id}_hb_{s}_{i}_{j}"
                        )
                        
                        result = await self._evaluate_parameters(session.model_name, param_set, resource_allocation=r_i)
                        if result:
                            session.all_results.append(result)
                            session.current_iteration += 1
                            
                            # Update best result
                            if (session.best_result is None or 
                                result.overall_score > session.best_result.overall_score):
                                session.best_result = result
                                session.convergence_history.append(result.overall_score)
                            
                            # Check early stopping
                            if self._should_stop_early(session):
                                break
                        
                        await asyncio.sleep(0.1)
                    
                    if self._should_stop_early(session):
                        break
                    
                    # Keep top 1/eta configurations
                    configs = configs[:n_i // eta]
                
                if self._should_stop_early(session):
                    break
                    
        except Exception as e:
            logger.error(f"Hyperband optimization failed: {e}")
            raise

    def _generate_grid_combinations(self, parameter_ranges: Dict[str, ParameterRange]) -> List[Dict[str, Any]]:
        """Generate all combinations for grid search."""
        combinations = []
        
        # Get all parameter values
        param_values = {}
        for param_name, param_range in parameter_ranges.items():
            if param_range.discrete_values:
                param_values[param_name] = param_range.discrete_values
            elif param_range.step:
                if param_range.log_scale:
                    # Log-scale steps
                    log_min = math.log(param_range.min_value)
                    log_max = math.log(param_range.max_value)
                    steps = int((log_max - log_min) / math.log(param_range.step)) + 1
                    values = [math.exp(log_min + i * math.log(param_range.step)) for i in range(steps)]
                else:
                    # Linear steps
                    steps = int((param_range.max_value - param_range.min_value) / param_range.step) + 1
                    values = [param_range.min_value + i * param_range.step for i in range(steps)]
                param_values[param_name] = values
            else:
                # Continuous range - discretize
                steps = 5  # Default discretization
                if param_range.log_scale:
                    log_min = math.log(param_range.min_value)
                    log_max = math.log(param_range.max_value)
                    values = [math.exp(log_min + i * (log_max - log_min) / (steps - 1)) for i in range(steps)]
                else:
                    values = [param_range.min_value + i * (param_range.max_value - param_range.min_value) / (steps - 1) for i in range(steps)]
                param_values[param_name] = values
        
        # Generate combinations
        from itertools import product
        param_names = list(param_values.keys())
        param_value_lists = [param_values[name] for name in param_names]
        
        for combination in product(*param_value_lists):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations

    def _generate_random_parameters(self, parameter_ranges: Dict[str, ParameterRange]) -> Dict[str, Any]:
        """Generate random parameters within the specified ranges."""
        params = {}
        
        for param_name, param_range in parameter_ranges.items():
            if param_range.discrete_values:
                params[param_name] = random.choice(param_range.discrete_values)
            else:
                if param_range.log_scale:
                    # Log-uniform sampling
                    log_min = math.log(param_range.min_value)
                    log_max = math.log(param_range.max_value)
                    log_value = random.uniform(log_min, log_max)
                    params[param_name] = math.exp(log_value)
                else:
                    # Uniform sampling
                    params[param_name] = random.uniform(param_range.min_value, param_range.max_value)
        
        return params

    def _generate_bayesian_parameters(self, session: OptimizationSession) -> Dict[str, Any]:
        """Generate parameters using Bayesian optimization principles."""
        # Simple implementation - in practice, you'd use a proper Bayesian optimization library
        # For now, we'll use a simple approach based on the best results so far
        
        if len(session.all_results) < 2:
            return self._generate_random_parameters(session.config.parameter_ranges)
        
        # Find the best result
        best_result = max(session.all_results, key=lambda x: x.overall_score)
        
        # Perturb the best parameters
        perturbed_params = {}
        for param_name, param_value in best_result.parameters.items():
            if param_name in session.config.parameter_ranges:
                param_range = session.config.parameter_ranges[param_name]
                
                if isinstance(param_value, (int, float)):
                    # Add noise
                    noise_factor = 0.1
                    if param_range.log_scale:
                        noise_factor = 0.2
                    
                    noise = random.uniform(-noise_factor, noise_factor) * param_value
                    perturbed_value = param_value + noise
                    
                    # Clamp to range
                    perturbed_value = max(param_range.min_value, min(param_range.max_value, perturbed_value))
                    
                    if param_range.step and isinstance(param_value, int):
                        perturbed_value = int(round(perturbed_value / param_range.step) * param_range.step)
                    
                    perturbed_params[param_name] = perturbed_value
                else:
                    perturbed_params[param_name] = param_value
            else:
                perturbed_params[param_name] = param_value
        
        return perturbed_params

    def _select_parents(self, results: List[OptimizationResult], num_parents: int) -> List[Dict[str, Any]]:
        """Select parents for evolutionary optimization."""
        if not results:
            return []
        
        # Sort by overall score
        sorted_results = sorted(results, key=lambda x: x.overall_score, reverse=True)
        
        # Tournament selection
        parents = []
        for _ in range(num_parents):
            # Random tournament
            tournament_size = min(3, len(sorted_results))
            tournament = random.sample(sorted_results, tournament_size)
            winner = max(tournament, key=lambda x: x.overall_score)
            parents.append(winner.parameters)
        
        return parents

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """Perform crossover between two parent parameter sets."""
        child = {}
        
        for param_name in parent1.keys():
            if random.random() < 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]
        
        return child

    def _mutate(self, params: Dict[str, Any], parameter_ranges: Dict[str, ParameterRange]) -> Dict[str, Any]:
        """Mutate parameters with some probability."""
        mutated_params = params.copy()
        
        for param_name, param_value in mutated_params.items():
            if param_name in parameter_ranges and random.random() < 0.1:  # 10% mutation rate
                param_range = parameter_ranges[param_name]
                
                if isinstance(param_value, (int, float)):
                    # Add noise
                    noise_factor = 0.2
                    if param_range.log_scale:
                        noise_factor = 0.3
                    
                    noise = random.uniform(-noise_factor, noise_factor) * param_value
                    mutated_value = param_value + noise
                    
                    # Clamp to range
                    mutated_value = max(param_range.min_value, min(param_range.max_value, mutated_value))
                    
                    if param_range.step and isinstance(param_value, int):
                        mutated_value = int(round(mutated_value / param_range.step) * param_range.step)
                    
                    mutated_params[param_name] = mutated_value
        
        return mutated_params

    async def _evaluate_parameters(self, model_name: str, param_set: ParameterSet, 
                                 resource_allocation: Optional[int] = None) -> Optional[OptimizationResult]:
        """Evaluate a set of parameters."""
        try:
            # Create test prompt
            test_prompt = "Write a brief summary of artificial intelligence in 2-3 sentences."
            
            # Measure generation time
            start_time = datetime.now()
            
            # Generate response
            response = await self._generate_with_parameters(model_name, test_prompt, param_set.parameters)
            
            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds() * 1000  # Convert to ms
            
            if not response:
                return None
            
            # Calculate metrics
            quality_score = self._calculate_quality_score(response, test_prompt)
            latency_ms = generation_time
            memory_usage_gb = self._estimate_memory_usage(param_set.parameters)
            throughput_tokens_per_sec = len(response.split()) / (generation_time / 1000)
            resource_efficiency = quality_score / (latency_ms / 1000)  # Quality per second
            
            # Calculate overall score based on objective
            overall_score = self._calculate_overall_score(
                quality_score, latency_ms, memory_usage_gb, throughput_tokens_per_sec, resource_efficiency
            )
            
            # Create result
            result = OptimizationResult(
                evaluation_id=param_set.evaluation_id,
                parameters=param_set.parameters,
                metrics={
                    "quality_score": quality_score,
                    "latency_ms": latency_ms,
                    "memory_usage_gb": memory_usage_gb,
                    "throughput_tokens_per_sec": throughput_tokens_per_sec,
                    "resource_efficiency": resource_efficiency
                },
                quality_score=quality_score,
                latency_ms=latency_ms,
                memory_usage_gb=memory_usage_gb,
                throughput_tokens_per_sec=throughput_tokens_per_sec,
                resource_efficiency=resource_efficiency,
                overall_score=overall_score,
                evaluation_time=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating parameters: {e}")
            return None

    async def _generate_with_parameters(self, model_name: str, prompt: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Generate text with specific parameters."""
        try:
            # Prepare payload
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": parameters
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Generation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating with parameters: {e}")
            return None

    def _calculate_quality_score(self, response: str, prompt: str) -> float:
        """Calculate a quality score for the response."""
        try:
            score = 0.0
            
            # Length score (0.2)
            if len(response) > 0:
                length_score = min(len(response) / 100, 0.2)  # Cap at 0.2 for responses > 100 chars
                score += length_score
            
            # Relevance score (0.3) - simple keyword matching
            prompt_keywords = set(prompt.lower().split())
            response_keywords = set(response.lower().split())
            
            if prompt_keywords:
                relevance = len(prompt_keywords.intersection(response_keywords)) / len(prompt_keywords)
                score += relevance * 0.3
            
            # Coherence score (0.3) - sentence structure
            sentences = response.split('.')
            if len(sentences) > 1:
                coherence_score = min(len(sentences) / 5, 0.3)  # Cap at 0.3 for 5+ sentences
                score += coherence_score
            
            # Grammar score (0.2) - basic checks
            if response and response[0].isupper() and response.endswith(('.', '!', '?')):
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5

    def _estimate_memory_usage(self, parameters: Dict[str, Any]) -> float:
        """Estimate memory usage based on parameters."""
        try:
            base_memory = 2.0  # Base memory in GB
            
            # Adjust based on context length
            if "num_ctx" in parameters:
                context_factor = parameters["num_ctx"] / 4096  # Normalize to 4K context
                base_memory *= context_factor
            
            # Adjust based on number of threads
            if "num_thread" in parameters:
                thread_factor = parameters["num_thread"] / 4  # Normalize to 4 threads
                base_memory *= thread_factor
            
            # Adjust based on GPU usage
            if "num_gpu" in parameters and parameters["num_gpu"] > 0:
                gpu_factor = 1.5  # GPU models use more memory
                base_memory *= gpu_factor
            
            return max(base_memory, 0.5)  # Minimum 0.5GB
            
        except Exception as e:
            logger.error(f"Error estimating memory usage: {e}")
            return 2.0

    def _calculate_overall_score(self, quality_score: float, latency_ms: float, 
                                memory_usage_gb: float, throughput_tokens_per_sec: float,
                                resource_efficiency: float) -> float:
        """Calculate overall score based on multiple metrics."""
        try:
            # Normalize metrics to 0-1 range
            normalized_quality = quality_score
            normalized_latency = max(0, 1 - (latency_ms / 10000))  # 10s = 0, 0s = 1
            normalized_memory = max(0, 1 - (memory_usage_gb / 16))  # 16GB = 0, 0GB = 1
            normalized_throughput = min(throughput_tokens_per_sec / 100, 1.0)  # 100 tokens/s = 1
            
            # Weighted combination
            overall_score = (
                normalized_quality * 0.4 +
                normalized_latency * 0.3 +
                normalized_memory * 0.2 +
                normalized_throughput * 0.1
            )
            
            return max(0, min(overall_score, 1.0))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return quality_score

    def _should_stop_early(self, session: OptimizationSession) -> bool:
        """Check if optimization should stop early."""
        if len(session.convergence_history) < session.config.early_stopping_patience:
            return False
        
        # Check if improvement is below threshold
        recent_history = session.convergence_history[-session.config.early_stopping_patience:]
        if len(recent_history) >= 2:
            improvement = recent_history[-1] - recent_history[0]
            if improvement < session.config.min_improvement:
                return True
        
        return False

    async def get_optimization_status(self, session_id: str) -> Optional[OptimizationSession]:
        """Get the status of an optimization session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        elif session_id in self.completed_sessions:
            return self.completed_sessions[session_id]
        return None

    async def list_optimization_sessions(self, status_filter: Optional[str] = None) -> List[OptimizationSession]:
        """List optimization sessions with optional status filter."""
        sessions = []
        
        if status_filter:
            sessions.extend([s for s in self.active_sessions.values() if s.status == status_filter])
            sessions.extend([s for s in self.completed_sessions.values() if s.status == status_filter])
        else:
            sessions.extend(self.active_sessions.values())
            sessions.extend(self.completed_sessions.values())
        
        # Sort by start time (newest first)
        sessions.sort(key=lambda x: x.start_time, reverse=True)
        return sessions

    async def get_best_parameters(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the best parameters from an optimization session."""
        session = await self.get_optimization_status(session_id)
        if session and session.best_result:
            return session.best_result.parameters
        return None

    async def get_optimization_history(self, session_id: str) -> List[OptimizationResult]:
        """Get the optimization history for a session."""
        session = await self.get_optimization_status(session_id)
        if session:
            return session.all_results
        return []

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("Ollama Parameter Optimizer cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Ollama Parameter Optimizer: {e}")

# Global instance for easy access
ollama_parameter_optimizer = OllamaParameterOptimizer()
