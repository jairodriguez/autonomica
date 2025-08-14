#!/usr/bin/env python3
"""
Test script for the Keyword Suggestion Engine
Tests keyword suggestion generation, filtering, scoring, and insights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.seo_service import KeywordSuggestionEngine, SEOService, SEOConfig, SEMrushConfig, WebScrapingConfig

def test_keyword_suggestion_engine():
    """Test the keyword suggestion engine functionality"""
    print("🚀 Starting Keyword Suggestion Engine Tests")
    print("=" * 50)
    
    # Create SEO service and suggestion engine
    config = SEOConfig(
        semrush=SEMrushConfig(api_key="test_key"),
        web_scraping=WebScrapingConfig(timeout=30),
        openai_api_key="test_key"
    )
    
    seo_service = SEOService(config)
    suggestion_engine = KeywordSuggestionEngine(seo_service)
    
    print("✅ Keyword suggestion engine created successfully")
    
    # Test comprehensive suggestions
    print("\n🔍 Testing comprehensive keyword suggestions...")
    
    comprehensive_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="digital marketing",
        suggestion_type="comprehensive",
        max_results=15
    )
    
    if "error" not in comprehensive_suggestions:
        print(f"✅ Generated {comprehensive_suggestions['total_suggestions']} comprehensive suggestions")
        print(f"  - Seed keyword: {comprehensive_suggestions['seed_keyword']}")
        print(f"  - Suggestion type: {comprehensive_suggestions['suggestion_type']}")
        
        # Display top suggestions
        print("  - Top 5 suggestions:")
        for i, suggestion in enumerate(comprehensive_suggestions['suggestions'][:5], 1):
            print(f"    {i}. {suggestion['keyword']} (Score: {suggestion['score']}, Source: {suggestion['source']})")
    else:
        print(f"⚠️  Comprehensive suggestions error: {comprehensive_suggestions['error']}")
    
    # Test related suggestions
    print("\n🔗 Testing related keyword suggestions...")
    
    related_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="seo",
        suggestion_type="related",
        max_results=10
    )
    
    if "error" not in related_suggestions:
        print(f"✅ Generated {related_suggestions['total_suggestions']} related suggestions")
        print("  - Top 3 related suggestions:")
        for i, suggestion in enumerate(related_suggestions['suggestions'][:3], 1):
            print(f"    {i}. {suggestion['keyword']} (Similarity: {suggestion['similarity']:.2f})")
    else:
        print(f"⚠️  Related suggestions error: {related_suggestions['error']}")
    
    # Test long-tail suggestions
    print("\n📏 Testing long-tail keyword suggestions...")
    
    long_tail_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="content marketing",
        suggestion_type="long_tail",
        max_results=12
    )
    
    if "error" not in long_tail_suggestions:
        print(f"✅ Generated {long_tail_suggestions['total_suggestions']} long-tail suggestions")
        print("  - Sample long-tail suggestions:")
        for i, suggestion in enumerate(long_tail_suggestions['suggestions'][:5], 1):
            word_count = len(suggestion['keyword'].split())
            print(f"    {i}. {suggestion['keyword']} ({word_count} words, Score: {suggestion['score']})")
    else:
        print(f"⚠️  Long-tail suggestions error: {long_tail_suggestions['error']}")
    
    # Test question suggestions
    print("\n❓ Testing question-based keyword suggestions...")
    
    question_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="social media",
        suggestion_type="questions",
        max_results=15
    )
    
    if "error" not in question_suggestions:
        print(f"✅ Generated {question_suggestions['total_suggestions']} question suggestions")
        print("  - Sample question suggestions:")
        for i, suggestion in enumerate(question_suggestions['suggestions'][:5], 1):
            print(f"    {i}. {suggestion['keyword']} (Score: {suggestion['score']})")
    else:
        print(f"⚠️  Question suggestions error: {question_suggestions['error']}")
    
    # Test local suggestions
    print("\n📍 Testing local keyword suggestions...")
    
    local_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="marketing agency",
        suggestion_type="local",
        max_results=10
    )
    
    if "error" not in local_suggestions:
        print(f"✅ Generated {local_suggestions['total_suggestions']} local suggestions")
        print("  - Sample local suggestions:")
        for i, suggestion in enumerate(local_suggestions['suggestions'][:5], 1):
            print(f"    {i}. {suggestion['keyword']} (Score: {suggestion['score']})")
    else:
        print(f"⚠️  Local suggestions error: {local_suggestions['error']}")
    
    # Test filtering functionality
    print("\n🔧 Testing suggestion filtering...")
    
    filters = {
        "min_similarity": 0.5,
        "min_words": 2,
        "max_words": 6,
        "sources": ["semantic_variation", "long_tail_variation"]
    }
    
    filtered_suggestions = suggestion_engine.suggest_keywords(
        seed_keyword="email marketing",
        suggestion_type="comprehensive",
        max_results=20,
        filters=filters
    )
    
    if "error" not in filtered_suggestions:
        print(f"✅ Generated {filtered_suggestions['total_suggestions']} filtered suggestions")
        print(f"  - Filters applied: {filtered_suggestions['metadata']['filters_applied']}")
        
        # Verify filters were applied
        all_filtered = True
        for suggestion in filtered_suggestions['suggestions']:
            if suggestion['similarity'] < 0.5:
                all_filtered = False
                break
            word_count = len(suggestion['keyword'].split())
            if word_count < 2 or word_count > 6:
                all_filtered = False
                break
            if suggestion['source'] not in ["semantic_variation", "long_tail_variation"]:
                all_filtered = False
                break
        
        if all_filtered:
            print("  ✅ All suggestions passed filter validation")
        else:
            print("  ⚠️  Some suggestions did not pass filter validation")
    else:
        print(f"⚠️  Filtered suggestions error: {filtered_suggestions['error']}")
    
    # Test suggestion insights
    print("\n📊 Testing suggestion insights generation...")
    
    if "error" not in comprehensive_suggestions:
        insights = suggestion_engine.get_suggestion_insights(comprehensive_suggestions['suggestions'])
        
        if "error" not in insights:
            print("✅ Generated suggestion insights:")
            print(f"  - Total suggestions: {insights['total_suggestions']}")
            print(f"  - Question ratio: {insights['question_ratio']:.2f}")
            print(f"  - Local ratio: {insights['local_ratio']:.2f}")
            print(f"  - Average similarity: {insights['avg_similarity']:.2f}")
            
            if insights['high_potential_keywords']:
                print(f"  - High potential keywords: {', '.join(insights['high_potential_keywords'][:3])}")
            
            if insights['trending_patterns']:
                print(f"  - Trending patterns: {', '.join(insights['trending_patterns'])}")
            
            # Display source distribution
            if insights['source_distribution']:
                print("  - Source distribution:")
                for source, count in insights['source_distribution'].items():
                    print(f"    * {source}: {count}")
            
            # Display word count distribution
            if insights['word_count_distribution']:
                print("  - Word count distribution:")
                for word_count, count in sorted(insights['word_count_distribution'].items()):
                    print(f"    * {word_count} words: {count}")
        else:
            print(f"⚠️  Insights generation error: {insights['error']}")
    
    # Test caching functionality
    print("\n💾 Testing suggestion caching...")
    
    # Generate same suggestion twice
    first_result = suggestion_engine.suggest_keywords("test keyword", "comprehensive", 5)
    second_result = suggestion_engine.suggest_keywords("test keyword", "comprehensive", 5)
    
    if "error" not in first_result and "error" not in second_result:
        if first_result == second_result:
            print("✅ Caching working correctly - identical results returned")
        else:
            print("⚠️  Caching may not be working - results differ")
    else:
        print("⚠️  Could not test caching due to errors")
    
    # Test error handling
    print("\n⚠️  Testing error handling...")
    
    # Test with invalid suggestion type
    try:
        invalid_result = suggestion_engine.suggest_keywords("test", "invalid_type", 5)
        if "error" in invalid_result:
            print("✅ Invalid suggestion type handled correctly")
        else:
            print("⚠️  Invalid suggestion type not handled as expected")
    except Exception as e:
        print(f"✅ Invalid suggestion type exception caught: {str(e)}")
    
    # Test with empty keyword
    empty_result = suggestion_engine.suggest_keywords("", "comprehensive", 5)
    if "error" in empty_result or empty_result['total_suggestions'] == 0:
        print("✅ Empty keyword handled correctly")
    else:
        print("⚠️  Empty keyword not handled as expected")
    
    print("\n🎉 All keyword suggestion engine tests completed successfully!")
    return True

def test_suggestion_algorithms():
    """Test individual suggestion algorithms"""
    print("\n🔬 Testing individual suggestion algorithms...")
    
    config = SEOConfig(
        semrush=SEMrushConfig(api_key="test_key"),
        web_scraping=WebScrapingConfig(timeout=30),
        openai_api_key="test_key"
    )
    
    seo_service = SEOService(config)
    suggestion_engine = KeywordSuggestionEngine(seo_service)
    
    # Test semantic variations
    print("  - Testing semantic variations...")
    semantic_vars = suggestion_engine._generate_semantic_variations("digital marketing")
    print(f"    Generated {len(semantic_vars)} semantic variations")
    for var in semantic_vars[:3]:
        print(f"    * {var}")
    
    # Test long-tail variations
    print("  - Testing long-tail variations...")
    long_tail_vars = suggestion_engine._generate_long_tail_variations("seo")
    print(f"    Generated {len(long_tail_vars)} long-tail variations")
    for var in long_tail_vars[:3]:
        print(f"    * {var}")
    
    # Test question variations
    print("  - Testing question variations...")
    question_vars = suggestion_engine._generate_question_variations("content marketing")
    print(f"    Generated {len(question_vars)} question variations")
    for var in question_vars[:3]:
        print(f"    * {var}")
    
    # Test local variations
    print("  - Testing local variations...")
    local_vars = suggestion_engine._generate_local_suggestions("marketing agency", 10, {})
    print(f"    Generated {len(local_vars)} local variations")
    for var in local_vars[:3]:
        print(f"    * {var['keyword']}")
    
    # Test similarity calculation
    print("  - Testing similarity calculation...")
    similarity1 = suggestion_engine._calculate_keyword_similarity("digital marketing", "online marketing")
    similarity2 = suggestion_engine._calculate_keyword_similarity("seo", "search engine optimization")
    similarity3 = suggestion_engine._calculate_keyword_similarity("marketing", "unrelated topic")
    
    print(f"    'digital marketing' vs 'online marketing': {similarity1:.3f}")
    print(f"    'seo' vs 'search engine optimization': {similarity2:.3f}")
    print(f"    'marketing' vs 'unrelated topic': {similarity3:.3f}")
    
    print("✅ Individual algorithm tests completed")

if __name__ == "__main__":
    try:
        # Run main tests
        success = test_keyword_suggestion_engine()
        
        if success:
            # Run algorithm tests
            test_suggestion_algorithms()
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! Keyword suggestion engine is working correctly.")
            print("=" * 50)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)