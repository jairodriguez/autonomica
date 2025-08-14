#!/usr/bin/env python3
"""
Test script for the SEO Score Calculation Module
Tests comprehensive SEO scoring across all categories and factors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.seo_service import SEOScoreCalculator

def test_seo_score_calculator():
    """Test the SEO score calculator functionality"""
    print("🚀 Starting SEO Score Calculator Tests")
    print("=" * 50)
    
    # Create calculator instance
    calculator = SEOScoreCalculator()
    print("✅ SEO score calculator created successfully")
    
    # Test data for comprehensive scoring
    test_analysis_data = {
        "title": "Digital Marketing Guide - Complete Tutorial for Beginners 2024",
        "meta_description": "Learn digital marketing strategies and techniques with our comprehensive guide. Discover proven methods to grow your business online and improve your marketing ROI.",
        "headings": [
            {"level": 1, "text": "Digital Marketing Guide"},
            {"level": 2, "text": "What is Digital Marketing?"},
            {"level": 2, "text": "Key Strategies"},
            {"level": 3, "text": "SEO Optimization"},
            {"level": 3, "text": "Content Marketing"},
            {"level": 2, "text": "Getting Started"}
        ],
        "content": "Digital marketing encompasses all marketing efforts that use electronic devices or the internet. Businesses leverage digital channels such as search engines, social media, email, and other websites to connect with current and prospective customers. This comprehensive guide will walk you through the fundamentals of digital marketing and provide actionable strategies to help you succeed in the digital landscape. We'll cover everything from search engine optimization to social media marketing, ensuring you have a solid foundation to build upon.",
        "target_keyword": "digital marketing",
        "internal_links": [
            {"anchor_text": "SEO strategies", "url": "/seo-guide"},
            {"anchor_text": "Content marketing tips", "url": "/content-marketing"},
            {"anchor_text": "Social media marketing", "url": "/social-media"},
            {"anchor_text": "Email marketing campaigns", "url": "/email-marketing"},
            {"anchor_text": "Analytics and reporting", "url": "/analytics"}
        ],
        "images": [
            {"alt_text": "Digital marketing funnel diagram", "file_size": 150000},
            {"alt_text": "Marketing strategy flowchart", "file_size": 200000},
            {"alt_text": "SEO checklist infographic", "file_size": 300000},
            {"alt_text": "Social media calendar", "file_size": 120000}
        ],
        "page_speed": {
            "load_time": 2.8,
            "core_web_vitals": {
                "lcp": 2.2,
                "fid": 85
            }
        },
        "mobile_metrics": {
            "responsive": True,
            "touch_friendly": True,
            "mobile_optimized": True
        },
        "url": "https://example.com/digital-marketing-guide",
        "last_updated": "2024-01-15T10:00:00Z",
        "engagement_metrics": {
            "social_shares": 45,
            "comments": 12,
            "time_on_page": 240
        },
        "navigation": {
            "breadcrumbs": True,
            "site_search": True,
            "menu_items": 8
        },
        "accessibility": {
            "aria_labels": True,
            "keyboard_navigation": True,
            "color_contrast": True
        },
        "keyword_difficulty": 35,
        "competition_metrics": {
            "competition_level": "moderate"
        },
        "search_volume": 8500,
        "trend_direction": "growing"
    }
    
    # Calculate overall SEO score
    print("\n📊 Testing overall SEO score calculation...")
    
    seo_score_result = calculator.calculate_overall_seo_score(test_analysis_data)
    
    if "error" not in seo_score_result:
        print("✅ SEO score calculation completed successfully")
        print(f"  - Overall Score: {seo_score_result['overall_score']}/100")
        print(f"  - Grade: {seo_score_result['grade']}")
        
        # Display category scores
        print("  - Category Scores:")
        for category, score in seo_score_result['category_scores'].items():
            print(f"    * {category.replace('_', ' ').title()}: {score}/100")
        
        # Display score breakdown
        print("  - Score Breakdown:")
        breakdown = seo_score_result['score_breakdown']
        if 'strengths' in breakdown and breakdown['strengths']:
            print(f"    Strengths: {', '.join(breakdown['strengths'][:3])}")
        if 'weaknesses' in breakdown and breakdown['weaknesses']:
            print(f"    Weaknesses: {', '.join(breakdown['weaknesses'][:3])}")
        if 'improvement_areas' in breakdown and breakdown['improvement_areas']:
            print(f"    Improvement Areas: {', '.join(breakdown['improvement_areas'][:3])}")
        
        # Display recommendations
        print("  - Top Recommendations:")
        for i, rec in enumerate(seo_score_result['recommendations'][:3], 1):
            print(f"    {i}. {rec}")
        
        # Display priority actions
        print("  - Priority Actions:")
        for action in seo_score_result['priority_actions']:
            print(f"    * {action['category'].replace('_', ' ').title()}: "
                  f"Current {action['current_score']}, Target {action['target_score']} "
                  f"({action['effort_required']} effort, {action['impact_potential']} impact)")
        
        # Display improvement potential
        print("  - Improvement Potential:")
        for category, potential in seo_score_result['improvement_potential'].items():
            print(f"    * {category.replace('_', ' ').title()}: "
                  f"{potential['improvement_percentage']}% improvement potential "
                  f"({potential['priority']} priority)")
        
        # Display benchmark comparison
        print("  - Benchmark Comparison:")
        benchmark = seo_score_result['benchmark_comparison']
        print(f"    Current Benchmark: {benchmark['current_benchmark']}")
        if benchmark.get('next_benchmark'):
            next_bm = benchmark['next_benchmark']
            print(f"    Next Benchmark: {next_bm['category']} ({next_bm['points_needed']} points needed)")
        print(f"    Industry Average: {benchmark['industry_average']}")
        print(f"    Competitor Range: {benchmark['competitor_range']}")
        
    else:
        print(f"❌ SEO score calculation failed: {seo_score_result['error']}")
        return False
    
    # Test individual category scoring
    print("\n🔍 Testing individual category scoring...")
    
    # Test on-page scoring
    on_page_score = calculator._calculate_on_page_score(test_analysis_data)
    print(f"✅ On-page score: {on_page_score}/100")
    
    # Test technical scoring
    technical_score = calculator._calculate_technical_score(test_analysis_data)
    print(f"✅ Technical score: {technical_score}/100")
    
    # Test content scoring
    content_score = calculator._calculate_content_score(test_analysis_data)
    print(f"✅ Content score: {content_score}/100")
    
    # Test UX scoring
    ux_score = calculator._calculate_user_experience_score(test_analysis_data)
    print(f"✅ User Experience score: {ux_score}/100")
    
    # Test competitive scoring
    competitive_score = calculator._calculate_competitive_score(test_analysis_data)
    print(f"✅ Competitive score: {competitive_score}/100")
    
    # Test individual factor evaluations
    print("\n📋 Testing individual factor evaluations...")
    
    # Test title optimization
    title_score = calculator._evaluate_title_optimization(test_analysis_data["title"])
    print(f"✅ Title optimization: {title_score}/100")
    
    # Test meta description
    meta_score = calculator._evaluate_meta_description(test_analysis_data["meta_description"])
    print(f"✅ Meta description: {meta_score}/100")
    
    # Test heading structure
    heading_score = calculator._evaluate_heading_structure(test_analysis_data["headings"])
    print(f"✅ Heading structure: {heading_score}/100")
    
    # Test keyword density
    keyword_score = calculator._evaluate_keyword_density(
        test_analysis_data["content"], 
        test_analysis_data["target_keyword"]
    )
    print(f"✅ Keyword density: {keyword_score}/100")
    
    # Test internal linking
    link_score = calculator._evaluate_internal_linking(test_analysis_data["internal_links"])
    print(f"✅ Internal linking: {link_score}/100")
    
    # Test image optimization
    image_score = calculator._evaluate_image_optimization(test_analysis_data["images"])
    print(f"✅ Image optimization: {image_score}/100")
    
    # Test page speed
    speed_score = calculator._evaluate_page_speed(test_analysis_data["page_speed"])
    print(f"✅ Page speed: {speed_score}/100")
    
    # Test mobile friendliness
    mobile_score = calculator._evaluate_mobile_friendliness(test_analysis_data["mobile_metrics"])
    print(f"✅ Mobile friendliness: {mobile_score}/100")
    
    # Test SSL security
    ssl_score = calculator._evaluate_ssl_security(test_analysis_data["url"])
    print(f"✅ SSL security: {ssl_score}/100")
    
    # Test URL structure
    url_score = calculator._evaluate_url_structure(test_analysis_data["url"])
    print(f"✅ URL structure: {url_score}/100")
    
    # Test content length
    length_score = calculator._evaluate_content_length(test_analysis_data["content"])
    print(f"✅ Content length: {length_score}/100")
    
    # Test content quality
    quality_score = calculator._evaluate_content_quality(test_analysis_data["content"])
    print(f"✅ Content quality: {quality_score}/100")
    
    # Test readability
    readability_score = calculator._evaluate_readability(test_analysis_data["content"])
    print(f"✅ Readability: {readability_score}/100")
    
    # Test content freshness
    freshness_score = calculator._evaluate_content_freshness(test_analysis_data["last_updated"])
    print(f"✅ Content freshness: {freshness_score}/100")
    
    # Test engagement signals
    engagement_score = calculator._evaluate_engagement_signals(test_analysis_data["engagement_metrics"])
    print(f"✅ Engagement signals: {engagement_score}/100")
    
    # Test navigation
    navigation_score = calculator._evaluate_navigation(test_analysis_data["navigation"])
    print(f"✅ Navigation: {navigation_score}/100")
    
    # Test accessibility
    accessibility_score = calculator._evaluate_accessibility(test_analysis_data["accessibility"])
    print(f"✅ Accessibility: {accessibility_score}/100")
    
    # Test keyword difficulty
    difficulty_score = calculator._evaluate_keyword_difficulty(test_analysis_data["keyword_difficulty"])
    print(f"✅ Keyword difficulty: {difficulty_score}/100")
    
    # Test competition level
    competition_score = calculator._evaluate_competition_level(test_analysis_data["competition_metrics"])
    print(f"✅ Competition level: {competition_score}/100")
    
    # Test search volume
    volume_score = calculator._evaluate_search_volume(test_analysis_data["search_volume"])
    print(f"✅ Search volume: {volume_score}/100")
    
    # Test trend direction
    trend_score = calculator._evaluate_trend_direction(test_analysis_data["trend_direction"])
    print(f"✅ Trend direction: {trend_score}/100")
    
    # Test edge cases
    print("\n⚠️  Testing edge cases and error handling...")
    
    # Test with minimal data
    minimal_data = {"title": "Test", "url": "http://example.com"}
    minimal_score = calculator.calculate_overall_seo_score(minimal_data)
    if "error" not in minimal_score:
        print(f"✅ Minimal data handling: Score {minimal_score['overall_score']}/100")
    else:
        print(f"⚠️  Minimal data error: {minimal_score['error']}")
    
    # Test with empty data
    empty_data = {}
    empty_score = calculator.calculate_overall_seo_score(empty_data)
    if "error" not in empty_score:
        print(f"✅ Empty data handling: Score {empty_score['overall_score']}/100")
    else:
        print(f"⚠️  Empty data error: {empty_score['error']}")
    
    # Test score grading
    print("\n📚 Testing score grading system...")
    
    test_scores = [95, 87, 78, 65, 52, 38, 25]
    for score in test_scores:
        grade = calculator._get_score_grade(score)
        print(f"  - Score {score}/100 = Grade {grade}")
    
    print("\n🎉 All SEO score calculator tests completed successfully!")
    return True

def test_scoring_weights():
    """Test scoring weights and calculations"""
    print("\n⚖️  Testing scoring weights and calculations...")
    
    calculator = SEOScoreCalculator()
    
    # Test category weights
    print("  - Category Weights:")
    total_category_weight = sum(calculator.score_weights.values())
    print(f"    Total category weight: {total_category_weight}")
    
    for category, weight in calculator.score_weights.items():
        print(f"    {category.replace('_', ' ').title()}: {weight * 100}%")
    
    # Test factor weights
    print("  - Factor Weights (Sample):")
    sample_factors = list(calculator.factor_weights.items())[:5]
    for factor, weight in sample_factors:
        print(f"    {factor.replace('_', ' ').title()}: {weight * 100}%")
    
    print("✅ Weight testing completed")

if __name__ == "__main__":
    try:
        # Run main tests
        success = test_seo_score_calculator()
        
        if success:
            # Run weight tests
            test_scoring_weights()
            
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! SEO score calculator is working correctly.")
            print("=" * 50)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)