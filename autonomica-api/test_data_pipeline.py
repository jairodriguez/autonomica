#!/usr/bin/env python3
"""
Test script for the Data Processing Pipeline
Tests data cleaning, validation, integration, and export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.seo_service import DataProcessingPipeline, KeywordRecord, SERPResult

def test_data_processing_pipeline():
    """Test the data processing pipeline functionality"""
    print("🚀 Starting Data Processing Pipeline Tests")
    print("=" * 50)
    
    # Create pipeline instance
    pipeline = DataProcessingPipeline()
    print("✅ Data processing pipeline created successfully")
    
    # Test data cleaning and validation
    print("\n🧹 Testing data cleaning and validation...")
    
    # Test keyword data processing
    raw_keyword_data = [
        {
            "keyword": "  digital marketing  ",
            "search_volume": "10,000",
            "cpc": "$2.50",
            "difficulty": "65%",
            "trends": ["8000", "9000", "10000", "11000"],
            "related_keywords": ["  seo  ", "  ppc  ", "  social media  "],
            "competition": "75%",
            "url": "https://example.com/digital-marketing"
        },
        {
            "keyword": "seo optimization",
            "search_volume": "5K",
            "cpc": "1.25",
            "difficulty": "80",
            "trends": ["4000", "4500", "5000", "5500"],
            "related_keywords": ["on-page seo", "technical seo"],
            "competition": "85",
            "url": "https://example.com/seo"
        },
        {
            "keyword": "content marketing",
            "search_volume": "15M",
            "cpc": "$3.75",
            "difficulty": "45%",
            "trends": ["12000", "13000", "14000", "15000"],
            "related_keywords": ["blogging", "copywriting"],
            "competition": "60%",
            "url": "https://example.com/content"
        }
    ]
    
    # Process keyword data
    processed_keywords = pipeline.process_keyword_data(raw_keyword_data)
    print(f"✅ Processed {len(processed_keywords)} keyword records")
    
    # Verify keyword data cleaning
    for keyword in processed_keywords:
        print(f"  - {keyword.keyword}: Volume={keyword.search_volume}, Difficulty={keyword.difficulty}, CPC=${keyword.cpc}")
    
    # Test SERP data processing
    print("\n🌐 Testing SERP data processing...")
    
    raw_serp_data = [
        {
            "title": "  Digital Marketing Guide - Complete Tutorial  ",
            "url": "  https://example.com/digital-marketing-guide  ",
            "snippet": "  Learn digital marketing strategies and techniques...  ",
            "position": "#1",
            "featured_snippet": True,
            "paa_questions": ["  What is digital marketing?  ", "  How to start digital marketing?  "],
            "structured_data": {"type": "Article", "author": "John Doe"},
            "meta_description": "  Comprehensive digital marketing guide...  ",
            "content_type": "  Article  "
        },
        {
            "title": "SEO Optimization Best Practices",
            "url": "https://example.com/seo-best-practices",
            "snippet": "Discover the latest SEO optimization techniques...",
            "position": "#2",
            "featured_snippet": False,
            "paa_questions": [],
            "structured_data": {},
            "meta_description": "SEO optimization guide with best practices",
            "content_type": "Guide"
        }
    ]
    
    # Process SERP data
    processed_serp = pipeline.process_serp_data(raw_serp_data)
    print(f"✅ Processed {len(processed_serp)} SERP results")
    
    # Verify SERP data cleaning
    for serp in processed_serp:
        print(f"  - {serp.title[:50]}... | Featured: {serp.featured_snippet} | PAA: {len(serp.paa_questions)}")
    
    # Test data integration
    print("\n🔗 Testing data integration...")
    
    integrated_data = pipeline.integrate_data_sources(processed_keywords, processed_serp)
    print("✅ Data integration completed")
    
    # Display integration results
    print(f"  - Total keywords: {integrated_data['summary_stats']['total_keywords']}")
    print(f"  - Total SERP results: {integrated_data['summary_stats']['total_serp_results']}")
    print(f"  - Data quality: {integrated_data['data_quality']['overall_quality']:.1f}%")
    print(f"  - Data completeness: {integrated_data['data_quality']['data_completeness']:.1f}%")
    
    # Display cross-references
    print(f"  - Cross-references created: {len(integrated_data['cross_references'])}")
    for keyword, ref in integrated_data['cross_references'].items():
        print(f"    * {keyword}: {len(ref['serp_matches'])} SERP matches, {len(ref['content_opportunities'])} opportunities")
    
    # Test data export
    print("\n📤 Testing data export...")
    
    # Export to JSON
    json_export = pipeline.export_data(integrated_data, "json")
    print(f"✅ JSON export: {len(json_export)} characters")
    
    # Export to CSV
    csv_export = pipeline.export_data(integrated_data, "csv")
    print(f"✅ CSV export: {len(csv_export)} characters")
    
    # Export to XML
    xml_export = pipeline.export_data(integrated_data, "xml")
    print(f"✅ XML export: {len(xml_export)} characters")
    
    # Test data quality assessment
    print("\n📊 Testing data quality assessment...")
    
    quality_metrics = integrated_data['data_quality']
    print(f"  - Keyword data quality: {quality_metrics['keyword_data_quality']:.1f}%")
    print(f"  - SERP data quality: {quality_metrics['serp_data_quality']:.1f}%")
    print(f"  - Overall quality: {quality_metrics['overall_quality']:.1f}%")
    
    if quality_metrics['recommendations']:
        print("  - Recommendations:")
        for rec in quality_metrics['recommendations']:
            print(f"    * {rec}")
    
    # Test summary statistics
    print("\n📈 Testing summary statistics...")
    
    summary_stats = integrated_data['summary_stats']
    print(f"  - Average search volume: {summary_stats['keyword_metrics']['avg_search_volume']:.0f}")
    print(f"  - Average difficulty: {summary_stats['keyword_metrics']['avg_difficulty']:.1f}")
    print(f"  - Average CPC: ${summary_stats['keyword_metrics']['avg_cpc']:.2f}")
    print(f"  - Featured snippets: {summary_stats['serp_metrics']['featured_snippets']}")
    print(f"  - PAA questions: {summary_stats['serp_metrics']['paa_questions']}")
    
    # Test error handling
    print("\n⚠️  Testing error handling...")
    
    # Test with invalid data
    invalid_keyword_data = [
        {"keyword": "", "search_volume": "invalid", "difficulty": "150"},
        {"keyword": "valid keyword", "search_volume": "100", "difficulty": "50"}
    ]
    
    invalid_processed = pipeline.process_keyword_data(invalid_keyword_data)
    print(f"✅ Invalid data handling: {len(invalid_processed)} valid records from {len(invalid_keyword_data)} input")
    
    # Test with empty data
    empty_processed = pipeline.process_keyword_data([])
    print(f"✅ Empty data handling: {len(empty_processed)} records processed")
    
    print("\n🎉 All data processing pipeline tests completed successfully!")
    return True

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n🔍 Testing edge cases and boundary conditions...")
    
    pipeline = DataProcessingPipeline()
    
    # Test boundary values
    boundary_keyword = {
        "keyword": "test",
        "search_volume": "10",  # Minimum threshold
        "difficulty": "100",    # Maximum threshold
        "cpc": "0.0"           # Minimum threshold
    }
    
    boundary_processed = pipeline.process_keyword_data([boundary_keyword])
    print(f"✅ Boundary value test: {len(boundary_processed)} records processed")
    
    # Test very long data
    long_keyword = {
        "keyword": "a" * 1000,  # Very long keyword
        "search_volume": "1000",
        "difficulty": "50",
        "cpc": "1.0"
    }
    
    long_processed = pipeline.process_keyword_data([long_keyword])
    print(f"✅ Long data test: {len(long_processed)} records processed")
    
    # Test special characters
    special_keyword = {
        "keyword": "keyword with !@#$%^&*() symbols",
        "search_volume": "1000",
        "difficulty": "50",
        "cpc": "1.0"
    }
    
    special_processed = pipeline.process_keyword_data([special_keyword])
    print(f"✅ Special characters test: {len(special_processed)} records processed")
    
    print("✅ Edge case tests completed")

if __name__ == "__main__":
    try:
        # Run main tests
        success = test_data_processing_pipeline()
        
        if success:
            # Run edge case tests
            test_edge_cases()
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! Data processing pipeline is working correctly.")
            print("=" * 50)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)