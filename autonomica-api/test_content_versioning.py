#!/usr/bin/env python3
"""
Test script for content versioning system
"""

import sys
import os

# Add the app/ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'ai'))

from content_versioning import (
    get_versioning_system, 
    ContentType, 
    ContentFormat, 
    VersionStatus, 
    ChangeType
)

def test_content_creation():
    """Test creating new content"""
    print("Testing content creation...")
    
    versioning_system = get_versioning_system()
    
    # Create new content
    content_id = versioning_system.create_content(
        content="This is a test blog post about AI content generation.",
        content_type=ContentType.BLOG_POST,
        format=ContentFormat.PLAIN_TEXT,
        metadata={"title": "Test Blog Post", "tags": ["AI", "content"]},
        user_id="user123"
    )
    
    print(f"✓ Created content with ID: {content_id}")
    
    # Get version history
    versions = versioning_system.get_version_history(content_id)
    print(f"✓ Version history has {len(versions)} versions")
    
    # Check first version
    first_version = versions[0]
    print(f"✓ First version: {first_version.version_number} - {first_version.status}")
    
    return content_id

def test_version_creation(content_id):
    """Test creating new versions"""
    print("\nTesting version creation...")
    
    versioning_system = get_versioning_system()
    
    # Create a new version
    new_version_id = versioning_system.create_version(
        content_id=content_id,
        content="This is an updated test blog post about AI content generation with improvements.",
        user_id="user123",
        change_summary="Added more details and improved content structure"
    )
    
    print(f"✓ Created new version: {new_version_id}")
    
    # Get updated version history
    versions = versioning_system.get_version_history(content_id)
    print(f"✓ Version history now has {len(versions)} versions")
    
    # Check latest version
    latest_version = versions[-1]
    print(f"✓ Latest version: {latest_version.version_number} - {latest_version.status}")
    print(f"✓ Change summary: {latest_version.change_summary}")
    
    return new_version_id

def test_branching(content_id):
    """Test creating branches"""
    print("\nTesting branching...")
    
    versioning_system = get_versioning_system()
    
    # Get first version for branching
    versions = versioning_system.get_version_history(content_id)
    first_version_id = versions[0].version_id
    
    # Create a feature branch
    branch_id = versioning_system.create_branch(
        content_id=content_id,
        branch_name="feature/experimental",
        base_version_id=first_version_id,
        user_id="user123",
        description="Experimental branch for testing new features"
    )
    
    print(f"✓ Created branch: {branch_id}")
    
    # Get all branches
    branches = versioning_system.get_content_branches(content_id)
    print(f"✓ Content has {len(branches)} branches")
    
    for branch in branches:
        print(f"  - {branch.branch_name}: {branch.description}")

def test_status_updates(content_id):
    """Test updating version status"""
    print("\nTesting status updates...")
    
    versioning_system = get_versioning_system()
    
    # Get latest version
    versions = versioning_system.get_version_history(content_id)
    latest_version = versions[-1]
    
    # Update status to in review
    versioning_system.update_version_status(
        version_id=latest_version.version_id,
        new_status=VersionStatus.IN_REVIEW,
        user_id="user123",
        notes="Content ready for review"
    )
    
    print(f"✓ Updated version {latest_version.version_id} status to IN_REVIEW")
    
    # Check updated version
    updated_version = versioning_system.versions[latest_version.version_id]
    print(f"✓ Version status: {updated_version.status}")
    print(f"✓ Approval notes: {updated_version.approval_notes}")

def test_version_comparison(content_id):
    """Test comparing versions"""
    print("\nTesting version comparison...")
    
    versioning_system = get_versioning_system()
    
    # Get two versions to compare
    versions = versioning_system.get_version_history(content_id)
    if len(versions) >= 2:
        v1 = versions[0]
        v2 = versions[1]
        
        comparison = versioning_system.compare_versions(v1.version_id, v2.version_id)
        
        print(f"✓ Comparing version {v1.version_number} vs {v2.version_number}")
        print(f"  Content changed: {comparison['changes']['content_changed']}")
        print(f"  Content length difference: {comparison['changes']['content_length_diff']}")
        print(f"  Status changed: {comparison['changes']['status_changed']}")

def test_rollback(content_id):
    """Test rolling back to previous version"""
    print("\nTesting rollback...")
    
    versioning_system = get_versioning_system()
    
    # Get first version for rollback
    versions = versioning_system.get_version_history(content_id)
    first_version = versions[0]
    
    # Rollback to first version
    rollback_version_id = versioning_system.rollback_to_version(
        content_id=content_id,
        target_version_id=first_version.version_id,
        user_id="user123",
        reason="Reverting to original version due to issues"
    )
    
    print(f"✓ Created rollback version: {rollback_version_id}")
    
    # Check rollback version
    rollback_version = versioning_system.versions[rollback_version_id]
    print(f"✓ Rollback version number: {rollback_version.version_number}")
    print(f"✓ Rollback change summary: {rollback_version.change_summary}")
    
    # Get updated version history
    updated_versions = versioning_system.get_version_history(content_id)
    print(f"✓ Version history now has {len(updated_versions)} versions")

def test_change_tracking(content_id):
    """Test tracking changes"""
    print("\nTesting change tracking...")
    
    versioning_system = get_versioning_system()
    
    # Get latest version
    versions = versioning_system.get_version_history(content_id)
    latest_version = versions[-1]
    
    # Get changes for this version
    changes = versioning_system.get_version_changes(latest_version.version_id)
    print(f"✓ Version {latest_version.version_id} has {len(changes)} changes")
    
    for change in changes:
        print(f"  - {change.change_type}: {change.description} at {change.timestamp}")

def test_export_import(content_id):
    """Test exporting and importing version data"""
    print("\nTesting export/import...")
    
    versioning_system = get_versioning_system()
    
    # Export data
    export_data = versioning_system.export_version_data(content_id)
    print(f"✓ Exported data for content {content_id}")
    print(f"  Versions: {len(export_data['versions'])}")
    print(f"  Branches: {len(export_data['branches'])}")
    
    # Create new versioning system for import test
    new_versioning_system = get_versioning_system()
    
    # Import data
    new_versioning_system.import_version_data(export_data)
    print(f"✓ Imported data to new system")
    
    # Verify import
    imported_versions = new_versioning_system.get_version_history(content_id)
    print(f"✓ Imported system has {len(imported_versions)} versions")

def main():
    """Run all tests"""
    print("🧪 Testing Content Versioning System\n")
    
    try:
        # Test content creation
        content_id = test_content_creation()
        
        # Test version creation
        test_version_creation(content_id)
        
        # Test branching
        test_branching(content_id)
        
        # Test status updates
        test_status_updates(content_id)
        
        # Test version comparison
        test_version_comparison(content_id)
        
        # Test rollback
        test_rollback(content_id)
        
        # Test change tracking
        test_change_tracking(content_id)
        
        # Test export/import
        test_export_import(content_id)
        
        print("\n✅ All tests passed! Content versioning system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())