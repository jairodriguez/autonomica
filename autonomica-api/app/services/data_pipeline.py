"""
Data Processing Pipeline for SEO Research and Analysis.

This module provides a comprehensive data processing pipeline that:
- Integrates data from multiple sources (SEMrush, web scraping, etc.)
- Cleans and normalizes data
- Handles data validation and quality checks
- Provides data transformation and enrichment
- Manages data flow and processing stages
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
from enum import Enum

from loguru import logger

from app.services.semrush_client import SEMrushClient, KeywordData, DomainData
from app.services.web_scraper import WebScraper, SERPData
from app.services.keyword_clustering import KeywordClusteringEngine
from app.services.keyword_analyzer import KeywordAnalyzer, KeywordAnalysis


class DataSource(Enum):
    """Enumeration of data sources."""
    SEMRUSH = "semrush"
    WEB_SCRAPING = "web_scraping"
    KEYWORD_CLUSTERING = "keyword_clustering"
    KEYWORD_ANALYSIS = "keyword_analysis"
    USER_INPUT = "user_input"


class ProcessingStage(Enum):
    """Enumeration of processing stages."""
    COLLECTION = "collection"
    CLEANING = "cleaning"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    INTEGRATION = "integration"
    EXPORT = "export"


@dataclass
class DataRecord:
    """Base data record for the pipeline."""
    record_id: str
    source: DataSource
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.record_id:
            self.record_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique record ID."""
        timestamp = str(int(time.time() * 1000000))
        source_str = self.source.value
        data_hash = hashlib.md5(json.dumps(self.data, sort_keys=True).encode()).hexdigest()[:8]
        return f"{source_str}_{timestamp}_{data_hash}"
    
    def update_quality_score(self, score: float):
        """Update quality score and timestamp."""
        self.quality_score = score
        self.updated_at = datetime.now()
    
    def add_validation_error(self, error: str):
        """Add validation error."""
        self.validation_errors.append(error)
        self.updated_at = datetime.now()


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    success: bool
    stage: ProcessingStage
    records_processed: int
    records_failed: int
    processing_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    output_data: Optional[Any] = None


class DataValidator:
    """Data validation and quality checking."""
    
    @staticmethod
    def validate_keyword_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate keyword data structure and content."""
        errors = []
        
        # Check required fields
        required_fields = ['keyword']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate keyword field
        if 'keyword' in data:
            keyword = data['keyword']
            if not isinstance(keyword, str) or len(keyword.strip()) == 0:
                errors.append("Keyword must be a non-empty string")
            elif len(keyword) > 200:
                errors.append("Keyword too long (max 200 characters)")
        
        # Validate numeric fields
        numeric_fields = ['search_volume', 'cpc', 'competition', 'keyword_difficulty']
        for field in numeric_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], (int, float)):
                    errors.append(f"{field} must be numeric")
                elif field == 'search_volume' and data[field] < 0:
                    errors.append("Search volume cannot be negative")
                elif field == 'cpc' and data[field] < 0:
                    errors.append("CPC cannot be negative")
                elif field == 'competition' and not (0 <= data[field] <= 1):
                    errors.append("Competition must be between 0 and 1")
                elif field == 'keyword_difficulty' and not (0 <= data[field] <= 100):
                    errors.append("Keyword difficulty must be between 0 and 100")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_domain_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate domain data structure and content."""
        errors = []
        
        # Check required fields
        if 'domain' not in data:
            errors.append("Missing required field: domain")
        
        # Validate domain field
        if 'domain' in data:
            domain = data['domain']
            if not isinstance(domain, str) or len(domain.strip()) == 0:
                errors.append("Domain must be a non-empty string")
            elif not domain.count('.') >= 1:
                errors.append("Invalid domain format")
        
        # Validate numeric fields
        numeric_fields = ['authority_score', 'organic_keywords', 'organic_traffic']
        for field in numeric_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], (int, float)):
                    errors.append(f"{field} must be numeric")
                elif data[field] < 0:
                    errors.append(f"{field} cannot be negative")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def calculate_quality_score(data: Dict[str, Any], validation_errors: List[str]) -> float:
        """Calculate data quality score (0-100)."""
        base_score = 100.0
        
        # Deduct points for validation errors
        error_penalty = len(validation_errors) * 10
        base_score -= error_penalty
        
        # Deduct points for missing optional fields
        optional_fields = ['search_volume', 'cpc', 'competition', 'keyword_difficulty']
        missing_fields = sum(1 for field in optional_fields if field not in data or data[field] is None)
        missing_penalty = missing_fields * 5
        base_score -= missing_penalty
        
        # Bonus for complete data
        if missing_fields == 0:
            base_score += 10
        
        return max(0.0, min(100.0, base_score))


class DataCleaner:
    """Data cleaning and normalization."""
    
    @staticmethod
    def clean_keyword_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize keyword data."""
        cleaned = data.copy()
        
        # Clean keyword field
        if 'keyword' in cleaned:
            cleaned['keyword'] = cleaned['keyword'].strip().lower()
        
        # Normalize numeric fields
        numeric_fields = ['search_volume', 'cpc', 'competition', 'keyword_difficulty']
        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                if isinstance(cleaned[field], str):
                    try:
                        cleaned[field] = float(cleaned[field])
                    except ValueError:
                        cleaned[field] = None
                
                # Round to appropriate precision
                if field in ['cpc', 'competition']:
                    cleaned[field] = round(cleaned[field], 4) if cleaned[field] is not None else None
                elif field in ['search_volume', 'keyword_difficulty']:
                    cleaned[field] = int(cleaned[field]) if cleaned[field] is not None else None
        
        # Handle missing values
        for field in numeric_fields:
            if field not in cleaned or cleaned[field] is None:
                cleaned[field] = None
        
        return cleaned
    
    @staticmethod
    def clean_domain_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize domain data."""
        cleaned = data.copy()
        
        # Clean domain field
        if 'domain' in cleaned:
            cleaned['domain'] = cleaned['domain'].strip().lower()
            # Remove protocol if present
            if cleaned['domain'].startswith(('http://', 'https://')):
                cleaned['domain'] = cleaned['domain'].split('://', 1)[1]
            # Remove trailing slash
            cleaned['domain'] = cleaned['domain'].rstrip('/')
        
        # Normalize numeric fields
        numeric_fields = ['authority_score', 'organic_keywords', 'organic_traffic']
        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                if isinstance(cleaned[field], str):
                    try:
                        cleaned[field] = int(cleaned[field])
                    except ValueError:
                        cleaned[field] = None
        
        return cleaned
    
    @staticmethod
    def remove_duplicates(records: List[DataRecord], key_field: str = 'keyword') -> List[DataRecord]:
        """Remove duplicate records based on a key field."""
        seen = set()
        unique_records = []
        
        for record in records:
            key_value = record.data.get(key_field)
            if key_value not in seen:
                seen.add(key_value)
                unique_records.append(record)
        
        return unique_records


class DataTransformer:
    """Data transformation and enrichment."""
    
    @staticmethod
    def transform_keyword_data(record: DataRecord) -> DataRecord:
        """Transform keyword data into standardized format."""
        transformed_data = {
            'keyword': record.data.get('keyword', ''),
            'search_volume': record.data.get('search_volume'),
            'cpc': record.data.get('cpc'),
            'competition': record.data.get('competition'),
            'keyword_difficulty': record.data.get('keyword_difficulty'),
            'source': record.source.value,
            'collected_at': record.created_at.isoformat()
        }
        
        # Add derived fields
        if transformed_data['search_volume'] and transformed_data['keyword_difficulty']:
            transformed_data['volume_difficulty_ratio'] = (
                transformed_data['search_volume'] / transformed_data['keyword_difficulty']
            )
        
        if transformed_data['cpc'] and transformed_data['search_volume']:
            transformed_data['estimated_monthly_value'] = (
                transformed_data['cpc'] * transformed_data['search_volume'] * 0.01  # 1% CTR estimate
            )
        
        record.data = transformed_data
        return record
    
    @staticmethod
    def enrich_with_serp_data(keyword_record: DataRecord, serp_data: SERPData) -> DataRecord:
        """Enrich keyword data with SERP analysis."""
        enriched_data = keyword_record.data.copy()
        
        # Add SERP features
        enriched_data['serp_features'] = [feature.feature_type for feature in serp_data.features]
        enriched_data['total_results'] = serp_data.total_results
        enriched_data['search_time'] = serp_data.search_time
        
        # Add competitor domains
        enriched_data['competitor_domains'] = [result.domain for result in serp_data.results[:10]]
        
        # Add related searches
        enriched_data['related_searches'] = serp_data.related_searches
        enriched_data['people_also_ask'] = serp_data.people_also_ask
        
        keyword_record.data = enriched_data
        keyword_record.updated_at = datetime.now()
        
        return keyword_record


class DataPipeline:
    """
    Main data processing pipeline.
    
    Features:
    - Multi-stage data processing
    - Data validation and quality checking
    - Data cleaning and normalization
    - Data transformation and enrichment
    - Data integration from multiple sources
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize the data pipeline."""
        self.validators = {
            'keyword': DataValidator.validate_keyword_data,
            'domain': DataValidator.validate_domain_data
        }
        
        self.cleaners = {
            'keyword': DataCleaner.clean_keyword_data,
            'domain': DataCleaner.clean_domain_data
        }
        
        self.transformers = {
            'keyword': DataTransformer.transform_keyword_data
        }
        
        self.processing_history: List[ProcessingResult] = []
        
        logger.info("Data pipeline initialized")
    
    async def process_keyword_research(self, 
                                    keywords: List[str],
                                    target_domain: Optional[str] = None,
                                    include_serp_analysis: bool = True) -> ProcessingResult:
        """
        Process keyword research data through the complete pipeline.
        
        Args:
            keywords: List of keywords to research
            target_domain: Target domain for analysis
            include_serp_analysis: Whether to include SERP analysis
            
        Returns:
            ProcessingResult with pipeline execution details
        """
        start_time = time.time()
        stage_results = []
        
        try:
            logger.info(f"Starting keyword research pipeline for {len(keywords)} keywords")
            
            # Stage 1: Data Collection
            collection_result = await self._collect_keyword_data(keywords)
            stage_results.append(collection_result)
            
            if not collection_result.success:
                return self._create_failed_result(
                    ProcessingStage.COLLECTION,
                    collection_result.errors,
                    time.time() - start_time
                )
            
            # Stage 2: Data Cleaning
            cleaning_result = await self._clean_data(collection_result.output_data)
            stage_results.append(cleaning_result)
            
            # Stage 3: Data Validation
            validation_result = await self._validate_data(cleaning_result.output_data)
            stage_results.append(validation_result)
            
            # Stage 4: Data Transformation
            transformation_result = await self._transform_data(validation_result.output_data)
            stage_results.append(transformation_result)
            
            # Stage 5: Data Enrichment
            if include_serp_analysis:
                enrichment_result = await self._enrich_with_serp_data(
                    transformation_result.output_data, keywords
                )
                stage_results.append(enrichment_result)
            
            # Stage 6: Data Integration
            integration_result = await self._integrate_data(
                stage_results[-1].output_data
            )
            stage_results.append(integration_result)
            
            processing_time = time.time() - start_time
            
            # Create final result
            result = ProcessingResult(
                success=True,
                stage=ProcessingStage.INTEGRATION,
                records_processed=len(integration_result.output_data),
                records_failed=0,
                processing_time=processing_time,
                output_data=integration_result.output_data
            )
            
            self.processing_history.append(result)
            logger.info(f"Keyword research pipeline completed successfully in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Keyword research pipeline failed: {e}")
            
            result = self._create_failed_result(
                ProcessingStage.INTEGRATION,
                [str(e)],
                processing_time
            )
            
            self.processing_history.append(result)
            return result
    
    async def _collect_keyword_data(self, keywords: List[str]) -> ProcessingResult:
        """Collect keyword data from various sources."""
        start_time = time.time()
        records = []
        errors = []
        
        try:
            # For now, create mock data since we don't have actual API clients
            # In production, this would integrate with SEMrush, web scraping, etc.
            for keyword in keywords:
                mock_data = {
                    'keyword': keyword,
                    'search_volume': 1000 + hash(keyword) % 9000,  # Mock volume
                    'cpc': 0.5 + (hash(keyword) % 50) / 10,  # Mock CPC
                    'competition': (hash(keyword) % 100) / 100,  # Mock competition
                    'keyword_difficulty': hash(keyword) % 100  # Mock difficulty
                }
                
                record = DataRecord(
                    record_id="",
                    source=DataSource.USER_INPUT,
                    data=mock_data
                )
                records.append(record)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.COLLECTION,
                records_processed=len(records),
                records_failed=0,
                processing_time=processing_time,
                output_data=records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.COLLECTION,
                records_processed=0,
                records_failed=len(keywords),
                processing_time=processing_time,
                errors=errors
            )
    
    async def _clean_data(self, records: List[DataRecord]) -> ProcessingResult:
        """Clean and normalize data."""
        start_time = time.time()
        cleaned_records = []
        errors = []
        
        try:
            for record in records:
                try:
                    # Determine data type and apply appropriate cleaner
                    if 'keyword' in record.data:
                        cleaned_data = DataCleaner.clean_keyword_data(record.data)
                        record.data = cleaned_data
                        cleaned_records.append(record)
                    elif 'domain' in record.data:
                        cleaned_data = DataCleaner.clean_domain_data(record.data)
                        record.data = cleaned_data
                        cleaned_records.append(record)
                    else:
                        cleaned_records.append(record)
                        
                except Exception as e:
                    errors.append(f"Failed to clean record {record.record_id}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.CLEANING,
                records_processed=len(cleaned_records),
                records_failed=len(errors),
                processing_time=processing_time,
                errors=errors,
                output_data=cleaned_records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.CLEANING,
                records_processed=0,
                records_failed=len(records),
                processing_time=processing_time,
                errors=errors
            )
    
    async def _validate_data(self, records: List[DataRecord]) -> ProcessingResult:
        """Validate data quality and structure."""
        start_time = time.time()
        validated_records = []
        errors = []
        
        try:
            for record in records:
                try:
                    # Determine data type and apply appropriate validator
                    if 'keyword' in record.data:
                        is_valid, validation_errors = DataValidator.validate_keyword_data(record.data)
                        if is_valid:
                            # Calculate quality score
                            quality_score = DataValidator.calculate_quality_score(
                                record.data, validation_errors
                            )
                            record.update_quality_score(quality_score)
                            validated_records.append(record)
                        else:
                            record.validation_errors = validation_errors
                            errors.extend(validation_errors)
                            validated_records.append(record)
                    elif 'domain' in record.data:
                        is_valid, validation_errors = DataValidator.validate_domain_data(record.data)
                        if is_valid:
                            quality_score = DataValidator.calculate_quality_score(
                                record.data, validation_errors
                            )
                            record.update_quality_score(quality_score)
                            validated_records.append(record)
                        else:
                            record.validation_errors = validation_errors
                            errors.extend(validation_errors)
                            validated_records.append(record)
                    else:
                        validated_records.append(record)
                        
                except Exception as e:
                    errors.append(f"Failed to validate record {record.record_id}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.VALIDATION,
                records_processed=len(validated_records),
                records_failed=len(errors),
                processing_time=processing_time,
                errors=errors,
                output_data=validated_records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.VALIDATION,
                records_processed=0,
                records_failed=len(records),
                processing_time=processing_time,
                errors=errors
            )
    
    async def _transform_data(self, records: List[DataRecord]) -> ProcessingResult:
        """Transform data into standardized format."""
        start_time = time.time()
        transformed_records = []
        errors = []
        
        try:
            for record in records:
                try:
                    # Apply appropriate transformer
                    if 'keyword' in record.data:
                        transformed_record = DataTransformer.transform_keyword_data(record)
                        transformed_records.append(transformed_record)
                    else:
                        transformed_records.append(record)
                        
                except Exception as e:
                    errors.append(f"Failed to transform record {record.record_id}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.TRANSFORMATION,
                records_processed=len(transformed_records),
                records_failed=len(errors),
                processing_time=processing_time,
                errors=errors,
                output_data=transformed_records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.TRANSFORMATION,
                records_processed=0,
                records_failed=len(records),
                processing_time=processing_time,
                errors=errors
            )
    
    async def _enrich_with_serp_data(self, records: List[DataRecord], keywords: List[str]) -> ProcessingResult:
        """Enrich data with SERP analysis."""
        start_time = time.time()
        enriched_records = []
        errors = []
        
        try:
            # For now, create mock SERP data
            # In production, this would use the WebScraper service
            for record in records:
                try:
                    # Create mock SERP data
                    mock_serp_data = SERPData(
                        query=record.data.get('keyword', ''),
                        total_results=1000000,
                        search_time=0.5,
                        results=[],
                        features=[],
                        related_searches=[],
                        people_also_ask=[],
                        timestamp=datetime.now(),
                        user_agent="Mock User Agent"
                    )
                    
                    # Enrich the record
                    enriched_record = DataTransformer.enrich_with_serp_data(record, mock_serp_data)
                    enriched_records.append(enriched_record)
                    
                except Exception as e:
                    errors.append(f"Failed to enrich record {record.record_id}: {e}")
                    enriched_records.append(record)
                    continue
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.ENRICHMENT,
                records_processed=len(enriched_records),
                records_failed=len(errors),
                processing_time=processing_time,
                errors=errors,
                output_data=enriched_records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.ENRICHMENT,
                records_processed=0,
                records_failed=len(records),
                processing_time=processing_time,
                errors=errors
            )
    
    async def _integrate_data(self, records: List[DataRecord]) -> ProcessingResult:
        """Integrate data from multiple sources."""
        start_time = time.time()
        integrated_records = []
        errors = []
        
        try:
            # Remove duplicates
            unique_records = DataCleaner.remove_duplicates(records, 'keyword')
            
            # Sort by quality score
            sorted_records = sorted(unique_records, key=lambda x: x.quality_score, reverse=True)
            
            integrated_records = sorted_records
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                stage=ProcessingStage.INTEGRATION,
                records_processed=len(integrated_records),
                records_failed=len(errors),
                processing_time=processing_time,
                errors=errors,
                output_data=integrated_records
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            errors.append(str(e))
            
            return ProcessingResult(
                success=False,
                stage=ProcessingStage.INTEGRATION,
                records_processed=0,
                records_failed=len(records),
                processing_time=processing_time,
                errors=errors
            )
    
    def _create_failed_result(self, stage: ProcessingStage, errors: List[str], processing_time: float) -> ProcessingResult:
        """Create a failed processing result."""
        return ProcessingResult(
            success=False,
            stage=stage,
            records_processed=0,
            records_failed=1,
            processing_time=processing_time,
            errors=errors
        )
    
    def get_processing_history(self) -> List[ProcessingResult]:
        """Get processing history."""
        return self.processing_history.copy()
    
    def export_pipeline_data(self, records: List[DataRecord], filepath: str = None) -> str:
        """Export pipeline data to JSON format."""
        export_data = []
        
        for record in records:
            record_data = {
                'record_id': record.record_id,
                'source': record.source.value,
                'data': record.data,
                'metadata': record.metadata,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat(),
                'quality_score': record.quality_score,
                'validation_errors': record.validation_errors
            }
            export_data.append(record_data)
        
        json_string = json.dumps(export_data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_string)
            return filepath
        else:
            return json_string


# Example usage and testing
async def test_data_pipeline():
    """Test the data processing pipeline."""
    try:
        # Initialize pipeline
        pipeline = DataPipeline()
        
        # Test keywords
        test_keywords = [
            "digital marketing",
            "SEO optimization",
            "content marketing",
            "social media marketing",
            "email marketing"
        ]
        
        print("Testing data processing pipeline...")
        
        # Process keyword research
        result = await pipeline.process_keyword_research(test_keywords)
        
        if result.success:
            print(f"✅ Pipeline completed successfully!")
            print(f"   Records processed: {result.records_processed}")
            print(f"   Processing time: {result.processing_time:.2f}s")
            
            # Export results
            json_output = pipeline.export_pipeline_data(result.output_data)
            print(f"   Output data length: {len(json_output)} characters")
            
        else:
            print(f"❌ Pipeline failed: {result.errors}")
        
        # Show processing history
        history = pipeline.get_processing_history()
        print(f"\nProcessing history: {len(history)} operations")
        
    except Exception as e:
        logger.error(f"Data pipeline test failed: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_data_pipeline())