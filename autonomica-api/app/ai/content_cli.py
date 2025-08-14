#!/usr/bin/env python3
"""
Command Line Interface for Content Generation and Repurposing Pipeline

This module provides a user-friendly CLI for interacting with the content
generation, repurposing, quality checking, and versioning systems.
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

# Import our content modules
from content_types_simple import ContentType, ContentFormat, get_content_registry
from content_generation import ContentGenerator, ContentGenerationRequest, ContentRepurposingRequest
from content_repurposing import get_repurposing_engine
from content_quality import get_quality_checker
from content_versioning import get_versioning_system, VersionStatus, ChangeType

# Configure content generator
content_generator = ContentGenerator()
repurposing_engine = get_repurposing_engine()
quality_checker = get_quality_checker()
versioning_system = get_versioning_system()


class ContentCLI:
    """Command Line Interface for content operations"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command line argument parser"""
        parser = argparse.ArgumentParser(
            description="Content Generation and Repurposing Pipeline CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate a blog post
  python content_cli.py generate --type blog_post --prompt "Write about AI in marketing" --format markdown
  
  # Repurpose blog to tweets
  python content_cli.py repurpose --from blog_post --to tweet --content "path/to/blog.txt"
  
  # Check content quality
  python content_cli.py quality --content "path/to/content.txt" --type blog_post
  
  # Create content version
  python content_cli.py version --action create --content "path/to/content.txt" --type blog_post
  
  # List available content types
  python content_cli.py types
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Generate command
        gen_parser = subparsers.add_parser('generate', help='Generate new content')
        gen_parser.add_argument('--type', required=True, help='Content type to generate')
        gen_parser.add_argument('--prompt', required=True, help='Generation prompt')
        gen_parser.add_argument('--format', default='plain_text', help='Output format')
        gen_parser.add_argument('--brand-voice', help='Brand voice guidelines')
        gen_parser.add_argument('--custom-instructions', help='Custom instructions')
        gen_parser.add_argument('--output', help='Output file path')
        
        # Repurpose command
        repurpose_parser = subparsers.add_parser('repurpose', help='Repurpose existing content')
        repurpose_parser.add_argument('--from', dest='from_type', required=True, help='Source content type')
        repurpose_parser.add_argument('--to', dest='to_type', required=True, help='Target content type')
        repurpose_parser.add_argument('--content', required=True, help='Content file path or text')
        repurpose_parser.add_argument('--strategy', help='Repurposing strategy')
        repurpose_parser.add_argument('--output', help='Output file path')
        
        # Quality command
        quality_parser = subparsers.add_parser('quality', help='Check content quality')
        quality_parser.add_argument('--content', required=True, help='Content file path or text')
        quality_parser.add_argument('--type', required=True, help='Content type')
        quality_parser.add_argument('--brand-voice', help='Brand voice for consistency check')
        quality_parser.add_argument('--output', help='Output file path')
        
        # Version command
        version_parser = subparsers.add_parser('version', help='Manage content versions')
        version_parser.add_argument('--action', required=True, choices=['create', 'list', 'compare', 'rollback'], help='Action to perform')
        version_parser.add_argument('--content', help='Content file path or text')
        version_parser.add_argument('--type', help='Content type')
        version_parser.add_argument('--content-id', help='Content ID for existing content')
        version_parser.add_argument('--version-id', help='Version ID for operations')
        version_parser.add_argument('--change-summary', help='Summary of changes')
        version_parser.add_argument('--output', help='Output file path')
        
        # Types command
        subparsers.add_parser('types', help='List available content types and formats')
        
        # Strategies command
        subparsers.add_parser('strategies', help='List available repurposing strategies')
        
        return parser
    
    def _read_content_from_file(self, file_path: str) -> str:
        """Read content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    
    def _write_output(self, content: str, output_path: Optional[str]) -> None:
        """Write content to output file or stdout"""
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Output written to: {output_path}")
            except Exception as e:
                print(f"Error writing to file: {e}")
                sys.exit(1)
        else:
            print("\n" + "="*50)
            print("GENERATED CONTENT")
            print("="*50)
            print(content)
            print("="*50)
    
    def _get_content_type(self, type_str: str) -> ContentType:
        """Get ContentType enum from string"""
        try:
            return ContentType(type_str)
        except ValueError:
            print(f"Error: Invalid content type '{type_str}'")
            print("Available types:")
            for ct in ContentType:
                print(f"  - {ct.value}")
            sys.exit(1)
    
    def _get_content_format(self, format_str: str) -> ContentFormat:
        """Get ContentFormat enum from string"""
        try:
            return ContentFormat(format_str)
        except ValueError:
            print(f"Error: Invalid format '{format_str}'")
            print("Available formats:")
            for cf in ContentFormat:
                print(f"  - {cf.value}")
            sys.exit(1)
    
    def generate_content(self, args) -> None:
        """Generate new content"""
        print("🎯 Generating content...")
        
        try:
            content_type = self._get_content_type(args.type)
            content_format = self._get_content_format(args.format)
            
            request = ContentGenerationRequest(
                content_type=content_type,
                target_format=content_format,
                prompt=args.prompt,
                brand_voice=args.brand_voice,
                custom_instructions=args.custom_instructions
            )
            
            response = content_generator.generate_content_sync(request)
            
            # Write the generated content
            self._write_output(response.content, args.output)
            
            # Show metadata
            print(f"\n📊 Generation Metadata:")
            print(f"  Model: {response.model_used}")
            print(f"  Tokens used: {response.token_usage.get('total_tokens', 'N/A') if response.token_usage else 'N/A'}")
            print(f"  Generation time: {response.generation_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Error during content generation: {e}")
            sys.exit(1)
    
    def repurpose_content(self, args) -> None:
        """Repurpose existing content"""
        print("🔄 Repurposing content...")
        
        try:
            from_type = self._get_content_type(args.from_type)
            to_type = self._get_content_type(args.to_type)
            
            # Read content
            if Path(args.content).is_file():
                content = self._read_content_from_file(args.content)
            else:
                content = args.content
            
            request = ContentRepurposingRequest(
                source_content=content,
                source_type=from_type,
                target_type=to_type,
                strategy=args.strategy
            )
            
            response = content_generator.repurpose_content_sync(request)
            
            # Write the repurposed content
            self._write_output(response.content, args.output)
            
            # Show metadata
            print(f"\n📊 Repurposing Metadata:")
            print(f"  Model: {response.model_used}")
            print(f"  Tokens used: {response.token_usage.get('total_tokens', 'N/A') if response.token_usage else 'N/A'}")
            print(f"  Repurposing time: {response.generation_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Error during content repurposing: {e}")
            sys.exit(1)
    
    def check_quality(self, args) -> None:
        """Check content quality"""
        print("🔍 Checking content quality...")
        
        try:
            content_type = self._get_content_type(args.type)
            
            # Read content
            if Path(args.content).is_file():
                content = self._read_content_from_file(args.content)
            else:
                content = args.content
            
            # Perform quality check
            report = quality_checker.assess_content_quality(
                content=content,
                content_type=content_type,
                target_format=ContentFormat.PLAIN_TEXT,  # Default format for quality check
                brand_voice=args.brand_voice
            )
            
            # Display results
            print(f"\n📊 Quality Report for {content_type.value}")
            print("="*60)
            print(f"Overall Score: {report.overall_score:.1f}/100 ({report.overall_level.value})")
            print(f"Summary: {report.summary}")
            
            print(f"\n📋 Detailed Scores:")
            for metric, score in report.metric_scores.items():
                print(f"  {metric.value}: {score.score:.1f}/100 ({score.level.value})")
                if score.details:
                    print(f"    Details: {score.details}")
            
            if report.recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(report.recommendations, 1):
                    print(f"  {i}. {rec}")
            
            # Write to file if requested
            if args.output:
                try:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(report.__dict__, f, indent=2, default=str)
                    print(f"\n📄 Quality report written to: {args.output}")
                except Exception as e:
                    print(f"Error writing report: {e}")
                    
        except Exception as e:
            print(f"❌ Error during quality check: {e}")
            sys.exit(1)
    
    def manage_versions(self, args) -> None:
        """Manage content versions"""
        print("📚 Managing content versions...")
        
        try:
            if args.action == 'create':
                if not args.content:
                    print("Error: --content is required for create action")
                    sys.exit(1)
                
                content_type = self._get_content_type(args.type) if args.type else ContentType.BLOG_POST
                
                # Read content
                if Path(args.content).is_file():
                    content = self._read_content_from_file(args.content)
                else:
                    content = args.content
                
                # Create new content or version
                if args.content_id:
                    # Create new version
                    version_id = versioning_system.create_version(
                        content_id=args.content_id,
                        content=content,
                        user_id="cli_user",
                        change_summary=args.change_summary or "Created via CLI"
                    )
                    print(f"✅ Created new version: {version_id}")
                else:
                    # Create new content
                    content_id = versioning_system.create_content(
                        content=content,
                        content_type=content_type,
                        format=ContentFormat.PLAIN_TEXT,
                        metadata={"source": "cli", "type": content_type.value},
                        user_id="cli_user"
                    )
                    print(f"✅ Created new content: {content_id}")
            
            elif args.action == 'list':
                if not args.content_id:
                    print("Error: --content-id is required for list action")
                    sys.exit(1)
                
                versions = versioning_system.get_version_history(args.content_id)
                print(f"\n📚 Version History for {args.content_id}:")
                print("="*60)
                
                for version in versions:
                    print(f"Version {version.version_number}:")
                    print(f"  ID: {version.version_id}")
                    print(f"  Status: {version.status.value}")
                    print(f"  Created: {version.created_at}")
                    print(f"  By: {version.created_by}")
                    if version.change_summary:
                        print(f"  Changes: {version.change_summary}")
                    print()
            
            elif args.action == 'compare':
                if not args.content_id or not args.version_id:
                    print("Error: --content-id and --version-id are required for compare action")
                    sys.exit(1)
                
                versions = versioning_system.get_version_history(args.content_id)
                if len(versions) < 2:
                    print("Error: Need at least 2 versions to compare")
                    sys.exit(1)
                
                # Compare latest with specified version
                latest_version = versions[-1]
                target_version = None
                for v in versions:
                    if v.version_id == args.version_id:
                        target_version = v
                        break
                
                if not target_version:
                    print(f"Error: Version {args.version_id} not found")
                    sys.exit(1)
                
                comparison = versioning_system.compare_versions(
                    target_version.version_id, 
                    latest_version.version_id
                )
                
                print(f"\n🔍 Version Comparison:")
                print("="*60)
                print(f"Comparing version {target_version.version_number} vs {latest_version.version_number}")
                print(f"Content changed: {comparison['changes']['content_changed']}")
                print(f"Content length difference: {comparison['changes']['content_length_diff']}")
                print(f"Status changed: {comparison['changes']['status_changed']}")
            
            elif args.action == 'rollback':
                if not args.content_id or not args.version_id:
                    print("Error: --content-id and --version-id are required for rollback action")
                    sys.exit(1)
                
                rollback_version_id = versioning_system.rollback_to_version(
                    content_id=args.content_id,
                    target_version_id=args.version_id,
                    user_id="cli_user",
                    reason=args.change_summary or "Rollback via CLI"
                )
                
                print(f"✅ Created rollback version: {rollback_version_id}")
                
        except Exception as e:
            print(f"❌ Error during version management: {e}")
            sys.exit(1)
    
    def list_types(self) -> None:
        """List available content types and formats"""
        print("📋 Available Content Types and Formats")
        print("="*60)
        
        print("\n🎯 Content Types:")
        for ct in ContentType:
            print(f"  - {ct.value}")
        
        print("\n📝 Content Formats:")
        for cf in ContentFormat:
            print(f"  - {cf.value}")
        
        print("\n🏗️  Content Structures:")
        registry = get_content_registry()
        for ct in ContentType:
            structure = registry.get_content_structure(ct)
            if structure:
                print(f"  {ct.value}:")
                print(f"    Required sections: {', '.join(structure.required_sections)}")
                print(f"    Word count range: {structure.word_count_range[0]}-{structure.word_count_range[1]}")
                if structure.character_limit:
                    print(f"    Character limit: {structure.character_limit}")
    
    def list_strategies(self) -> None:
        """List available repurposing strategies"""
        print("🔄 Available Repurposing Strategies")
        print("="*60)
        
        strategies = repurposing_engine.get_all_strategies()
        
        for strategy in strategies:
            print(f"\n📋 {strategy.name}:")
            print(f"  Description: {strategy.description}")
            print(f"  Complexity: {strategy.complexity}")
            print(f"  Estimated time: {strategy.estimated_time} seconds")
            print(f"  Quality impact: {strategy.quality_impact}")
            print(f"  Output format: {strategy.output_format.value}")
    
    def run(self, args=None) -> None:
        """Run the CLI with the given arguments"""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        try:
            if parsed_args.command == 'generate':
                self.generate_content(parsed_args)
            elif parsed_args.command == 'repurpose':
                self.repurpose_content(parsed_args)
            elif parsed_args.command == 'quality':
                self.check_quality(parsed_args)
            elif parsed_args.command == 'version':
                self.manage_versions(parsed_args)
            elif parsed_args.command == 'types':
                self.list_types()
            elif parsed_args.command == 'strategies':
                self.list_strategies()
            else:
                print(f"Unknown command: {parsed_args.command}")
                self.parser.print_help()
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    cli = ContentCLI()
    cli.run()


if __name__ == "__main__":
    main()