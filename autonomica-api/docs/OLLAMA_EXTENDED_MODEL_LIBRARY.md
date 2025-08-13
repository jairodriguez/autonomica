# Ollama Extended Model Library System

## Overview

The Ollama Extended Model Library System provides comprehensive model management capabilities for local AI models, including specialized model support, compatibility checking, intelligent recommendations, fine-tuning workflows, and parameter optimization.

## 🚀 Features

### Core Model Library Management
- **Categorized Model Organization**: Models organized by capability (general, code, vision, math, etc.)
- **Intelligent Search**: Advanced search with filters for category, size, performance, and parameters
- **Model Recommendations**: AI-powered suggestions based on task type and system capabilities
- **Compatibility Checking**: Automatic assessment of model compatibility with current hardware
- **Model Comparison**: Side-by-side comparison of multiple models with detailed metrics

### Fine-Tuning System
- **Custom Model Training**: Create specialized models from base models
- **Hyperparameter Presets**: Pre-configured training configurations (efficient, balanced, high-quality)
- **Training Data Validation**: Automatic validation of training data format and quality
- **Progress Tracking**: Real-time monitoring of training phases and metrics
- **Model Deployment**: Automatic deployment of fine-tuned models

### Parameter Optimization
- **Multiple Optimization Strategies**: Grid search, random search, Bayesian optimization, evolutionary, Hyperband
- **Custom Objectives**: Optimize for quality, speed, memory usage, or balanced performance
- **Resource-Aware Optimization**: Considers system constraints during optimization
- **Performance Metrics**: Comprehensive evaluation of model performance
- **Best Parameter Discovery**: Automatic identification of optimal parameter combinations

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Extended Model Library                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Model Library   │  │ Fine-Tuning     │  │ Parameter   │ │
│  │ Manager         │  │ Manager         │  │ Optimizer   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    API Layer (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│                    Ollama Integration                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Model Discovery**: System scans available Ollama models and categorizes them
2. **Capability Analysis**: Models are analyzed for their strengths and limitations
3. **Recommendation Engine**: AI-powered suggestions based on task requirements
4. **Compatibility Assessment**: Hardware requirements and system constraints evaluation
5. **Fine-Tuning Pipeline**: Automated training workflow with validation
6. **Optimization Engine**: Parameter tuning for optimal performance

## 📚 API Reference

### Model Library Endpoints

#### Get Model Library
```http
GET /api/ai/ollama/models/library
```
Returns comprehensive model library information organized by categories.

**Response:**
```json
{
  "success": true,
  "categories": {
    "general": [
      {
        "name": "llama3.1:8b",
        "size": "8B",
        "capabilities": ["text_generation", "instruction_following"],
        "performance_score": 0.85,
        "memory_requirements_gb": 4.2
      }
    ],
    "code": [
      {
        "name": "codellama:7b",
        "size": "7B",
        "capabilities": ["code_generation", "code_explanation"],
        "performance_score": 0.92,
        "memory_requirements_gb": 3.8
      }
    ]
  }
}
```

#### Search Models
```http
GET /api/ai/ollama/models/search?query={query}&category={category}&size={size}&min_performance={score}&max_parameters={count}
```

**Parameters:**
- `query`: Search term for model names and descriptions
- `category`: Filter by model category (general, code, vision, math)
- `size`: Filter by model size (tiny, small, medium, large, huge)
- `min_performance`: Minimum performance score (0.0 to 1.0)
- `max_parameters`: Maximum parameter count

**Response:**
```json
{
  "success": true,
  "query": "llama",
  "filters": {"category": "general"},
  "results": [
    {
      "name": "llama3.1:8b",
      "category": "general",
      "size": "8B",
      "performance_score": 0.85,
      "relevance_score": 0.95
    }
  ],
  "count": 1
}
```

#### Get Model Recommendations
```http
GET /api/ai/ollama/models/recommendations?task_type={type}&preferred_size={size}
```

**Parameters:**
- `task_type`: Type of task (code_generation, creative_writing, analysis, etc.)
- `preferred_size`: Preferred model size (optional)

**Response:**
```json
{
  "success": true,
  "task_type": "code_generation",
  "system_info": {
    "available_memory_gb": 16.0,
    "gpu_available": true,
    "gpu_memory_gb": 8.0
  },
  "recommendations": [
    {
      "model_name": "codellama:7b",
      "confidence_score": 0.95,
      "reasoning": "Specialized for code generation with optimal size for available resources",
      "expected_performance": 0.92,
      "alternatives": ["llama3.1:8b", "mistral:7b"],
      "trade_offs": "Slightly larger than alternatives but better code generation"
    }
  ]
}
```

#### Check Model Compatibility
```http
GET /api/ai/ollama/models/compatibility/{model_name}
```

**Response:**
```json
{
  "success": true,
  "model_name": "llama3.1:8b",
  "compatibility": {
    "compatibility_score": 0.92,
    "hardware_compatibility": {
      "memory": "compatible",
      "gpu": "compatible",
      "cpu": "compatible"
    },
    "warnings": [],
    "recommendations": ["Consider using GPU for better performance"],
    "performance_estimate": "Good performance expected with current hardware"
  }
}
```

#### Compare Models
```http
GET /api/ai/ollama/models/compare?models={model1},{model2},{model3}
```

**Response:**
```json
{
  "success": true,
  "models": ["llama3.1:8b", "codellama:7b", "mistral:7b"],
  "comparison_table": {
    "performance": {
      "llama3.1:8b": 0.85,
      "codellama:7b": 0.92,
      "mistral:7b": 0.88
    },
    "memory_usage": {
      "llama3.1:8b": 4.2,
      "codellama:7b": 3.8,
      "mistral:7b": 4.0
    }
  },
  "recommendations": [
    "codellama:7b is best for code generation tasks",
    "llama3.1:8b provides good general performance",
    "mistral:7b offers balanced performance and efficiency"
  ]
}
```

### Fine-Tuning Endpoints

#### Create Fine-Tuning Job
```http
POST /api/ai/ollama/fine-tuning/create
```

**Form Data:**
- `base_model`: Name of the base model to fine-tune
- `target_model_name`: Name for the new fine-tuned model
- `training_data_path`: Path to training data file
- `data_type`: Type of training data (jsonl, csv, text, conversation)
- `hyperparameters`: Hyperparameter preset or JSON string
- `target_capabilities`: JSON array of target capabilities

**Response:**
```json
{
  "success": true,
  "job_id": "0",
  "status": "pending",
  "message": "Fine-tuning job created successfully"
}
```

#### Start Fine-Tuning
```http
POST /api/ai/ollama/fine-tuning/start/{job_id}
```

#### Get Fine-Tuning Status
```http
GET /api/ai/ollama/fine-tuning/status/{job_id}
```

**Response:**
```json
{
  "success": true,
  "job": {
    "job_id": "0",
    "base_model": "llama3.1:8b",
    "target_model_name": "test-finetuned-model",
    "status": "training",
    "current_phase": "training",
    "progress": 0.65,
    "start_time": "2024-01-15T10:30:00",
    "logs": ["Epoch 2/3 completed. Loss: 0.3000, Accuracy: 0.8000"]
  }
}
```

#### List Fine-Tuning Jobs
```http
GET /api/ai/ollama/fine-tuning/jobs?status={status}
```

### Parameter Optimization Endpoints

#### Create Optimization Session
```http
POST /api/ai/ollama/optimization/create
```

**Form Data:**
- `model_name`: Name of the model to optimize
- `objective`: Optimization objective (maximize_quality, minimize_latency, etc.)
- `strategy`: Optimization strategy (bayesian_optimization, grid_search, etc.)
- `model_type`: Type of model for parameter ranges (general, code, creative, analysis)

**Response:**
```json
{
  "success": true,
  "session_id": "0",
  "model_name": "llama3.1:8b",
  "objective": "balance_quality_speed",
  "strategy": "bayesian_optimization",
  "message": "Optimization session created successfully"
}
```

#### Start Optimization
```http
POST /api/ai/ollama/optimization/start/{session_id}
```

#### Get Optimization Status
```http
GET /api/ai/ollama/optimization/status/{session_id}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "0",
    "model_name": "llama3.1:8b",
    "status": "running",
    "objective": "balance_quality_speed",
    "strategy": "bayesian_optimization",
    "current_iteration": 15,
    "best_result": {
      "overall_score": 0.87,
      "parameters": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_ctx": 4096
      }
    }
  }
}
```

#### List Optimization Sessions
```http
GET /api/ai/ollama/optimization/sessions?status={status}
```

#### Get Best Parameters
```http
GET /api/ai/ollama/optimization/best-parameters/{session_id}
```

## 🎯 Usage Examples

### Basic Model Discovery

```python
import httpx

async def discover_models():
    async with httpx.AsyncClient() as client:
        # Get all available models
        response = await client.get("http://localhost:8000/api/ai/ollama/models/library")
        models = response.json()
        
        # Search for code generation models
        search_response = await client.get(
            "http://localhost:8000/api/ai/ollama/models/search",
            params={"query": "code", "category": "code"}
        )
        code_models = search_response.json()
        
        return models, code_models
```

### Get Model Recommendations

```python
async def get_recommendations():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/ai/ollama/models/recommendations",
            params={"task_type": "code_generation"}
        )
        
        recommendations = response.json()
        best_model = recommendations["recommendations"][0]["model_name"]
        return best_model
```

### Create Fine-Tuning Job

```python
async def create_fine_tuning():
    async with httpx.AsyncClient() as client:
        job_data = {
            "base_model": "llama3.1:8b",
            "target_model_name": "my-specialized-model",
            "training_data_path": "/path/to/training_data.jsonl",
            "data_type": "jsonl",
            "hyperparameters": "balanced",
            "target_capabilities": json.dumps(["text_generation", "instruction_following"])
        }
        
        response = await client.post(
            "http://localhost:8000/api/ai/ollama/fine-tuning/create",
            data=job_data
        )
        
        job = response.json()
        return job["job_id"]
```

### Optimize Model Parameters

```python
async def optimize_parameters():
    async with httpx.AsyncClient() as client:
        # Create optimization session
        session_data = {
            "model_name": "llama3.1:8b",
            "objective": "maximize_quality",
            "strategy": "bayesian_optimization",
            "model_type": "general"
        }
        
        response = await client.post(
            "http://localhost:8000/api/ai/ollama/optimization/create",
            data=session_data
        )
        
        session = response.json()
        session_id = session["session_id"]
        
        # Start optimization
        await client.post(f"http://localhost:8000/api/ai/ollama/optimization/start/{session_id}")
        
        return session_id
```

## 🔧 Configuration

### Environment Variables

```bash
# Ollama connection
OLLAMA_BASE_URL=http://localhost:11434

# Storage paths
TASKMASTER_BASE_PATH=.taskmaster
FINE_TUNING_PATH=.taskmaster/fine_tuning
PERFORMANCE_DATA_PATH=.taskmaster/ollama_performance_data

# Optimization settings
MAX_OPTIMIZATION_ITERATIONS=100
OPTIMIZATION_TIMEOUT_MINUTES=60
```

### Model Library Configuration

The system automatically detects and categorizes models based on:
- Model names and descriptions
- Performance characteristics
- Capability patterns
- Resource requirements

### Fine-Tuning Configuration

**Hyperparameter Presets:**

1. **Efficient**: Fast training with minimal resources
   - Learning rate: 2e-5
   - Batch size: 2
   - Epochs: 2
   - Warmup steps: 50

2. **Balanced**: Good balance of speed and quality
   - Learning rate: 1e-5
   - Batch size: 4
   - Epochs: 3
   - Warmup steps: 100

3. **High Quality**: Maximum quality with longer training
   - Learning rate: 5e-6
   - Batch size: 8
   - Epochs: 5
   - Warmup steps: 200

### Parameter Optimization Configuration

**Optimization Strategies:**

1. **Grid Search**: Systematic exploration of parameter space
2. **Random Search**: Random sampling for quick exploration
3. **Bayesian Optimization**: Intelligent parameter selection using ML
4. **Evolutionary**: Genetic algorithm-based optimization
5. **Hyperband**: Resource-efficient hyperparameter optimization

**Optimization Objectives:**

1. **Maximize Quality**: Focus on response quality
2. **Minimize Latency**: Optimize for speed
3. **Minimize Memory**: Reduce resource usage
4. **Balance Quality/Speed**: Trade-off optimization
5. **Maximize Throughput**: Optimize for high-volume processing

## 📊 Performance Metrics

### Model Performance Scoring

The system evaluates models based on:
- **Quality Score**: Response relevance and coherence (0.0 to 1.0)
- **Latency**: Response generation time in milliseconds
- **Memory Usage**: Estimated memory requirements in GB
- **Throughput**: Tokens generated per second
- **Resource Efficiency**: Quality per unit of resource usage

### Fine-Tuning Metrics

- **Training Loss**: Model learning progress
- **Validation Accuracy**: Model generalization capability
- **Training Time**: Total training duration
- **Resource Utilization**: CPU, GPU, and memory usage
- **Convergence**: Training stability and progress

### Optimization Metrics

- **Overall Score**: Combined performance metric
- **Convergence History**: Optimization progress over time
- **Parameter Sensitivity**: Impact of parameter changes
- **Resource Efficiency**: Performance per resource unit
- **Trade-off Analysis**: Quality vs. speed vs. memory

## 🚨 Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid parameters or data format
- **404 Not Found**: Model or job not found
- **422 Validation Error**: Invalid input data
- **500 Internal Server Error**: System or processing error

### Error Response Format

```json
{
  "success": false,
  "error": "Detailed error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Troubleshooting

1. **Model Not Found**: Verify model name and Ollama connection
2. **Training Data Issues**: Check data format and file paths
3. **Resource Constraints**: Verify available memory and GPU
4. **Optimization Failures**: Check parameter ranges and constraints

## 🔒 Security Considerations

- **Authentication**: All endpoints require valid user authentication
- **Input Validation**: Comprehensive validation of all input parameters
- **Resource Limits**: Configurable limits on training and optimization
- **Data Privacy**: Training data is processed locally
- **Access Control**: User-based access to models and jobs

## 🚀 Getting Started

### Prerequisites

1. **Ollama Installation**: Install and configure Ollama
2. **Python Dependencies**: Install required Python packages
3. **System Resources**: Ensure adequate memory and storage
4. **API Access**: Valid authentication credentials

### Quick Start

1. **Start the API**:
   ```bash
   cd autonomica-api
   python -m uvicorn app.main:app --reload
   ```

2. **Discover Models**:
   ```bash
   curl "http://localhost:8000/api/ai/ollama/models/library"
   ```

3. **Get Recommendations**:
   ```bash
   curl "http://localhost:8000/api/ai/ollama/models/recommendations?task_type=code_generation"
   ```

4. **Create Fine-Tuning Job**:
   ```bash
   curl -X POST "http://localhost:8000/api/ai/ollama/fine-tuning/create" \
        -F "base_model=llama3.1:8b" \
        -F "target_model_name=my-model" \
        -F "training_data_path=/path/to/data.jsonl" \
        -F "data_type=jsonl"
   ```

### Testing

Run the comprehensive test suite:

```bash
cd autonomica-api
python test_extended_model_library.py
```

## 🔮 Future Enhancements

### Planned Features

1. **Advanced Model Analytics**: Deep performance analysis and insights
2. **Automated Model Selection**: AI-powered model recommendation engine
3. **Distributed Training**: Multi-node fine-tuning support
4. **Model Versioning**: Version control for fine-tuned models
5. **Performance Benchmarking**: Automated model evaluation suite
6. **Integration APIs**: Third-party tool and service integration

### Extensibility

The system is designed for easy extension:
- **Custom Model Categories**: Add new model types and capabilities
- **Custom Optimization Strategies**: Implement new optimization algorithms
- **Custom Metrics**: Define new performance evaluation criteria
- **Plugin System**: Modular architecture for additional features

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Performance Monitoring Guide](OLLAMA_PERFORMANCE_MONITORING.md)
- [API Reference Documentation](API_REFERENCE.md)

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Documentation updates
- Issue reporting

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This documentation is for the Extended Model Library System version 1.0. For the latest updates and changes, please refer to the project repository.
