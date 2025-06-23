"""
LangChain Integration for OWL Framework
Enhanced NLP capabilities and adapters for the Autonomica Workforce
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from loguru import logger

# LangChain imports
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.chains import (
    LLMChain, 
    ConversationChain,
    RetrievalQA,
    AnalyzeDocumentChain
)
from langchain.chains.summarize import load_summarize_chain
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# NLP-specific imports
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Install with: pip install transformers")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Install with: pip install nltk")


@dataclass
class NLPCapability:
    """NLP capability definition"""
    name: str
    description: str
    function_name: str
    input_type: str
    output_type: str
    required_tools: List[str] = field(default_factory=list)


@dataclass
class LangChainExecution:
    """Track LangChain execution results"""
    id: str
    agent_id: str
    capability: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    tokens_used: int
    cost: float
    execution_time: float
    status: str  # success, failed, timeout
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class AutonomicaCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for tracking LangChain operations"""
    
    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
        self.token_count = 0
        self.step_logs = []
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts running"""
        logger.info(f"Agent {self.agent_id}: Starting LLM with {len(prompts)} prompts")
        
    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM ends running"""
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            self.token_count += token_usage.get('total_tokens', 0)
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain starts running"""
        chain_name = serialized.get('name', 'Unknown Chain')
        self.step_logs.append(f"Started {chain_name}")
        
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when tool starts running"""
        tool_name = serialized.get('name', 'Unknown Tool')
        self.step_logs.append(f"Using tool: {tool_name}")


class LangChainNLPEngine:
    """Enhanced NLP engine using LangChain for advanced language processing"""
    
    def __init__(self):
        self.llm = None
        self.chat_model = None
        self.embeddings = None
        self.vector_store = None
        self.nlp_models = {}
        self.capabilities = {}
        self.executions: List[LangChainExecution] = []
        
        # Initialize NLP capabilities
        self._initialize_capabilities()
        
    async def initialize(self, api_key: str, model_name: str = "gpt-4o-mini"):
        """Initialize LangChain components"""
        try:
            # Initialize LangChain models
            self.llm = OpenAI(
                api_key=api_key,
                model_name=model_name,
                temperature=0.7,
                max_tokens=1000
            )
            
            self.chat_model = ChatOpenAI(
                api_key=api_key,
                model_name=model_name,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(api_key=api_key)
            
            # Initialize traditional NLP models
            await self._initialize_nlp_models()
            
            logger.info(f"LangChain NLP Engine initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain NLP Engine: {e}")
            raise
    
    def _initialize_capabilities(self):
        """Initialize available NLP capabilities"""
        self.capabilities = {
            "text_summarization": NLPCapability(
                name="Text Summarization",
                description="Summarize long texts into concise summaries",
                function_name="summarize_text",
                input_type="text",
                output_type="summary",
                required_tools=["llm"]
            ),
            "sentiment_analysis": NLPCapability(
                name="Sentiment Analysis", 
                description="Analyze emotional tone and sentiment in text",
                function_name="analyze_sentiment",
                input_type="text",
                output_type="sentiment_score",
                required_tools=["nltk", "transformers"]
            ),
            "entity_extraction": NLPCapability(
                name="Named Entity Recognition",
                description="Extract named entities from text",
                function_name="extract_entities",
                input_type="text", 
                output_type="entities",
                required_tools=["spacy"]
            ),
            "question_answering": NLPCapability(
                name="Question Answering",
                description="Answer questions based on provided context",
                function_name="answer_question",
                input_type="question_context",
                output_type="answer",
                required_tools=["llm", "embeddings"]
            ),
            "document_analysis": NLPCapability(
                name="Document Analysis",
                description="Comprehensive analysis of documents",
                function_name="analyze_document",
                input_type="document",
                output_type="analysis",
                required_tools=["llm", "embeddings", "chains"]
            ),
            "language_translation": NLPCapability(
                name="Language Translation",
                description="Translate text between languages",
                function_name="translate_text",
                input_type="text_language",
                output_type="translated_text",
                required_tools=["llm"]
            ),
            "conversation_management": NLPCapability(
                name="Conversation Management",
                description="Manage multi-turn conversations with memory",
                function_name="manage_conversation",
                input_type="conversation",
                output_type="response",
                required_tools=["chat_model", "memory"]
            ),
            "text_classification": NLPCapability(
                name="Text Classification",
                description="Classify text into predefined categories",
                function_name="classify_text",
                input_type="text",
                output_type="classification",
                required_tools=["transformers", "llm"]
            )
        }
    
    async def _initialize_nlp_models(self):
        """Initialize traditional NLP models"""
        try:
            # Initialize NLTK components if available
            if NLTK_AVAILABLE:
                try:
                    import nltk
                    nltk.download('vader_lexicon', quiet=True)
                    nltk.download('punkt', quiet=True)
                    nltk.download('stopwords', quiet=True)
                    nltk.download('wordnet', quiet=True)
                    
                    self.nlp_models['sentiment_analyzer'] = SentimentIntensityAnalyzer()
                    self.nlp_models['lemmatizer'] = WordNetLemmatizer()
                    logger.info("NLTK models initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize NLTK models: {e}")
            
            # Initialize spaCy model if available
            if SPACY_AVAILABLE:
                try:
                    import spacy
                    self.nlp_models['spacy'] = spacy.load("en_core_web_sm")
                    logger.info("spaCy model initialized successfully")
                except OSError:
                    logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                    self.nlp_models['spacy'] = None
            
            # Initialize Transformers pipelines if available
            if TRANSFORMERS_AVAILABLE:
                try:
                    from transformers import pipeline
                    self.nlp_models['classification_pipeline'] = pipeline(
                        "text-classification",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                    logger.info("Transformers models initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Transformers models: {e}")
            
        except Exception as e:
            logger.error(f"Failed to initialize traditional NLP models: {e}")
            # Continue without traditional models if they fail
    
    async def summarize_text(
        self, 
        text: str, 
        agent_id: str,
        max_length: int = 150,
        style: str = "concise"
    ) -> LangChainExecution:
        """Summarize text using LangChain"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            callback_handler = AutonomicaCallbackHandler(agent_id)
            
            # Create summarization chain
            prompt = ChatPromptTemplate.from_template(
                f"Summarize the following text in a {style} manner, "
                f"keeping it under {max_length} words:\n\n{{text}}"
            )
            
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Execute summarization
            summary = await chain.ainvoke(
                {"text": text},
                config={"callbacks": [callback_handler]}
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = LangChainExecution(
                id=execution_id,
                agent_id=agent_id,
                capability="text_summarization",
                input_data={"text": text[:500] + "..." if len(text) > 500 else text, "max_length": max_length, "style": style},
                output_data={"summary": summary, "original_length": len(text), "summary_length": len(summary)},
                tokens_used=callback_handler.token_count,
                cost=self._calculate_cost(callback_handler.token_count),
                execution_time=execution_time,
                status="success"
            )
            
            self.executions.append(execution)
            return execution
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = LangChainExecution(
                id=execution_id,
                agent_id=agent_id,
                capability="text_summarization",
                input_data={"text": text[:500] + "..." if len(text) > 500 else text},
                output_data={},
                tokens_used=0,
                cost=0.0,
                execution_time=execution_time,
                status="failed",
                error_message=str(e)
            )
            
            self.executions.append(execution)
            logger.error(f"Text summarization failed for agent {agent_id}: {e}")
            return execution
    
    async def analyze_sentiment(self, text: str, agent_id: str) -> LangChainExecution:
        """Analyze sentiment using both traditional and LLM approaches"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            results = {}
            
            # NLTK sentiment analysis
            if 'sentiment_analyzer' in self.nlp_models:
                nltk_scores = self.nlp_models['sentiment_analyzer'].polarity_scores(text)
                results['nltk_sentiment'] = {
                    'compound': nltk_scores['compound'],
                    'positive': nltk_scores['pos'],
                    'negative': nltk_scores['neg'],
                    'neutral': nltk_scores['neu']
                }
            
            # Transformers sentiment analysis
            if 'classification_pipeline' in self.nlp_models:
                hf_result = self.nlp_models['classification_pipeline'](text)[0]
                results['transformers_sentiment'] = {
                    'label': hf_result['label'],
                    'confidence': hf_result['score']
                }
            
            # LangChain LLM sentiment analysis
            callback_handler = AutonomicaCallbackHandler(agent_id)
            
            prompt = ChatPromptTemplate.from_template(
                "Analyze the sentiment of the following text. "
                "Provide a detailed analysis including overall sentiment (positive/negative/neutral), "
                "confidence score (0-1), key emotional indicators, and reasoning:\n\n{text}"
            )
            
            chain = prompt | self.chat_model | StrOutputParser()
            llm_analysis = await chain.ainvoke(
                {"text": text},
                config={"callbacks": [callback_handler]}
            )
            
            results['llm_sentiment'] = {
                'analysis': llm_analysis,
                'tokens_used': callback_handler.token_count
            }
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = LangChainExecution(
                id=execution_id,
                agent_id=agent_id,
                capability="sentiment_analysis",
                input_data={"text": text},
                output_data=results,
                tokens_used=callback_handler.token_count,
                cost=self._calculate_cost(callback_handler.token_count),
                execution_time=execution_time,
                status="success"
            )
            
            self.executions.append(execution)
            return execution
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = LangChainExecution(
                id=execution_id,
                agent_id=agent_id,
                capability="sentiment_analysis",
                input_data={"text": text},
                output_data={},
                tokens_used=0,
                cost=0.0,
                execution_time=execution_time,
                status="failed",
                error_message=str(e)
            )
            
            self.executions.append(execution)
            logger.error(f"Sentiment analysis failed for agent {agent_id}: {e}")
            return execution
    
    def _calculate_cost(self, tokens: int, model: str = "gpt-4o-mini") -> float:
        """Calculate cost based on token usage"""
        # Simplified cost calculation (assuming roughly equal input/output tokens)
        pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4": {"input": 0.03, "output": 0.06}
        }
        
        model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
        avg_price = (model_pricing["input"] + model_pricing["output"]) / 2
        
        return (tokens * avg_price) / 1000
    
    def get_capabilities(self) -> Dict[str, NLPCapability]:
        """Get all available NLP capabilities"""
        return self.capabilities
    
    def get_execution_history(self, agent_id: Optional[str] = None) -> List[LangChainExecution]:
        """Get execution history, optionally filtered by agent"""
        if agent_id:
            return [exec for exec in self.executions if exec.agent_id == agent_id]
        return self.executions
    
    def get_cost_summary(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost summary for executions"""
        executions = self.get_execution_history(agent_id)
        
        total_cost = sum(exec.cost for exec in executions)
        total_tokens = sum(exec.tokens_used for exec in executions)
        
        capability_stats = {}
        for exec in executions:
            cap = exec.capability
            if cap not in capability_stats:
                capability_stats[cap] = {"count": 0, "cost": 0.0, "tokens": 0}
            capability_stats[cap]["count"] += 1
            capability_stats[cap]["cost"] += exec.cost
            capability_stats[cap]["tokens"] += exec.tokens_used
        
        return {
            "total_executions": len(executions),
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "capability_breakdown": capability_stats,
            "agent_id": agent_id
        }


# Global NLP engine instance
_nlp_engine: Optional[LangChainNLPEngine] = None


async def get_nlp_engine() -> LangChainNLPEngine:
    """Get or create the global NLP engine instance"""
    global _nlp_engine
    
    if _nlp_engine is None:
        _nlp_engine = LangChainNLPEngine()
        # Initialize with OpenAI API key (should come from config)
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            await _nlp_engine.initialize(api_key)
        else:
            logger.warning("OPENAI_API_KEY not found, LangChain features may not work")
    
    return _nlp_engine 