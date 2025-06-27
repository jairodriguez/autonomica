# Agent Roles Specification - OWL/CAMEL Multi-Agent System

## Overview
This document defines the specialized agent roles implemented for the Autonomica OWL/CAMEL multi-agent marketing automation system. Each agent is designed with specific capabilities, tools, and models optimized for their domain expertise.

## Agent Role Definitions

### 1. CEO Agent
**Type:** `ceo`  
**Model:** `gpt-4o` (Premium reasoning for executive decisions)  
**Status:** Enhanced for OWL orchestration

**Primary Responsibilities:**
- Strategic leadership and workflow orchestration
- Multi-agent task delegation using CAMEL protocol
- Cost monitoring and token usage guardrails
- High-level oversight and quality control
- Client relations and stakeholder communication
- Resource allocation and task prioritization

**Capabilities:**
- `strategic_leadership` - Executive decision making
- `team_coordination` - Multi-agent coordination 
- `task_delegation` - Intelligent task assignment
- `cost_monitoring` - Token usage and budget control
- `client_relations` - Stakeholder communication
- `workflow_orchestration` - CAMEL protocol management

**Tools:** `search`, `document_processing`, `excel`, `retrieval`

---

### 2. SEO Researcher  
**Type:** `seo_researcher`  
**Model:** `gpt-4o-mini` (Cost-effective for research tasks)  
**Status:** Enhanced for comprehensive research

**Primary Responsibilities:**
- High-value keyword discovery and analysis
- Competitor analysis and content gap identification
- SERP feature analysis and ranking opportunities
- Technical SEO audit recommendations
- Local SEO and geo-targeted strategies

**Capabilities:**
- `keyword_research` - Advanced keyword discovery
- `competitor_analysis` - Market and competitor insights
- `serp_analysis` - Search results analysis
- `technical_seo` - Technical optimization
- `local_seo_research` - Local search optimization

**Tools:** `search`, `browser`, `excel`, `document_processing`, `retrieval`

---

### 3. Content Strategist
**Type:** `content_strategist`  
**Model:** `gpt-4o` (Strategic planning requires premium reasoning)  
**Status:** NEW - Added for comprehensive content planning

**Primary Responsibilities:**
- Content strategy development and planning
- Editorial workflow design and governance
- Topic clustering and content hub development
- Content audit and gap analysis
- Performance measurement strategies

**Capabilities:**
- `content_strategy` - Strategic content planning
- `content_planning` - Editorial calendar management
- `topic_clustering` - Content organization
- `content_audit` - Portfolio analysis
- `editorial_workflow` - Process design
- `content_governance` - Quality frameworks

**Tools:** `search`, `browser`, `document_processing`, `excel`, `retrieval`

---

### 4. Content Creator
**Type:** `content_creator`  
**Model:** `gpt-4o` (High-quality content creation)  
**Status:** Enhanced for SEO-optimized content

**Primary Responsibilities:**
- Long-form content creation (blogs, articles, whitepapers)
- SEO-optimized content writing with keyword integration
- Technical and thought leadership content
- Research-driven content with authoritative sources
- Brand voice consistency and storytelling

**Capabilities:**
- `blog_writing` - Blog post creation
- `article_creation` - Long-form articles
- `seo_content_writing` - SEO-optimized writing
- `technical_writing` - Technical documentation
- `storytelling` - Narrative development
- `research_writing` - Evidence-based content

**Tools:** `search`, `browser`, `document_processing`, `file_write`, `retrieval`

---

### 5. Content Repurposer
**Type:** `content_repurposer`  
**Model:** `gpt-4o-mini` (Format transformation, cost-effective)  
**Status:** NEW - Added for multi-format content adaptation

**Primary Responsibilities:**
- Transform long-form content into multiple formats
- Social media content adaptation and optimization
- Platform-specific content formatting
- Visual content planning and quote card creation
- Email newsletter and presentation development

**Capabilities:**
- `content_transformation` - Format conversion
- `social_content_creation` - Social media adaptation
- `visual_content_planning` - Visual asset planning
- `multi_format_adaptation` - Cross-platform optimization
- `platform_optimization` - Platform-specific formatting

**Tools:** `document_processing`, `file_write`, `search`, `browser`

---

### 6. Social Media Manager
**Type:** `social_media_manager`  
**Model:** `gpt-4o-mini` (High-volume social tasks)  
**Status:** Enhanced for platform-specific strategies

**Primary Responsibilities:**
- Platform-specific strategy development
- Community engagement and social listening
- Content calendar and posting optimization
- Hashtag research and trending topic identification
- Influencer collaboration and crisis management

**Capabilities:**
- `social_strategy` - Platform strategy development
- `content_scheduling` - Optimal timing planning
- `community_management` - Audience engagement
- `social_advertising` - Campaign planning
- `hashtag_research` - Trending topic analysis
- `social_analytics` - Performance measurement

**Tools:** `search`, `browser`, `twitter`, `linkedin`, `document_processing`, `excel`

---

### 7. Data Analyst
**Type:** `data_analyst`  
**Model:** `gpt-4o-mini` (Data processing, cost-effective)  
**Status:** Enhanced for comprehensive marketing analytics

**Primary Responsibilities:**
- Marketing performance analysis across channels
- Customer behavior analytics and user journey mapping
- Campaign ROI measurement and attribution modeling
- A/B testing design and statistical analysis
- Predictive analytics and forecasting

**Capabilities:**
- `marketing_analytics` - Performance analysis
- `performance_measurement` - KPI tracking
- `data_visualization` - Visual reporting
- `predictive_analytics` - Forecasting
- `roi_analysis` - Return on investment
- `conversion_optimization` - Funnel analysis

**Tools:** `excel`, `code_execution`, `document_processing`, `file_write`, `math`

---

## Architecture Design Principles

### Model Selection Strategy
- **Premium Models (gpt-4o):** Used for strategic thinking, complex reasoning, and high-quality content creation
- **Cost-Effective Models (gpt-4o-mini):** Used for research, data processing, and high-volume tasks
- **Optimization:** Balanced performance and cost based on task complexity

### Tool Assignment Logic
- **Research Tools:** `search`, `browser`, `retrieval` for information gathering
- **Processing Tools:** `document_processing`, `excel` for data manipulation
- **Creation Tools:** `file_write` for content generation
- **Social Tools:** `twitter`, `linkedin` for platform-specific tasks
- **Analytics Tools:** `code_execution`, `math` for data analysis

### CAMEL Protocol Integration
- All agents designed for inter-agent communication
- CEO Agent serves as orchestrator with delegation capabilities
- Role-based prompt templates ensure consistent behavior
- Task decomposition logic built into agent capabilities

### Cost Management
- Token usage monitoring built into CEO Agent role
- Model selection optimized for cost-effectiveness
- Guardrails implemented to prevent budget overruns
- Performance tracking for ROI optimization

## Implementation Status
✅ **Completed - Task 5.1:** All 6 specialized agent roles defined with enhanced capabilities  
🔄 **Next:** Task 5.2 - Design Agent Architecture  

## Next Steps
1. Design agent architecture and communication patterns
2. Implement CAMEL protocol for agent-to-agent messaging
3. Create agent initialization and bootstrapping logic
4. Develop task assignment and tracking systems
5. Implement error handling and recovery mechanisms 