#!/usr/bin/env python3
"""Fix critical files needed for Cherry AI deployment"""

import os
import ast
from pathlib import Path

# Critical files needed for deployment
CRITICAL_FILES = [
    "src/api/main.py",
    "src/search_engine/search_router.py",
    "src/search_engine/normal_search.py",
    "src/search_engine/creative_search.py",
    "src/search_engine/deep_search.py",
    "src/search_engine/super_deep_search.py",
    "src/search_engine/uncensored_search.py",
    "src/file_ingestion/ingestion_controller.py",
    "src/file_ingestion/document_parser.py",
    "src/file_ingestion/audio_transcriber.py",
    "src/file_ingestion/video_processor.py",
    "src/file_ingestion/zip_extractor.py",
    "src/multimedia_generation/image_gen_controller.py",
    "src/multimedia_generation/video_gen_controller.py",
    "src/multimedia_generation/operator_mode_coordinator.py",
    "src/operator_mode/operator_manager.py",
    "src/operator_mode/agent_supervisor.py",
    "src/operator_mode/agent_task_queue.py",
    "src/utils/circuit_breaker.py",
    "core/config.py",
    "core/main.py",
    "core/api/main.py",
    "agent/app/main.py",
]

def fix_indentation_errors(filepath):
    """Fix common indentation errors in Python files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fix common patterns
        fixed_lines = []
        for i, line in enumerate(lines):
            # Skip empty lines
            if line.strip() == '':
                fixed_lines.append(line)
                continue
                
            # Fix lines that start with unexpected indent
            if i > 0 and line.startswith('    ') and lines[i-1].strip() == '':
                # This might be a function or class definition
                if any(keyword in line for keyword in ['def ', 'class ', 'async def ']):
                    fixed_lines.append(line.lstrip())
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        # Verify it's valid Python now
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
            
        return True
    except Exception as e:
        print(f"  Failed to fix {filepath}: {e}")
        return False

def main():
    """Fix critical files for deployment"""
    print("🔧 Fixing critical files for Cherry AI deployment...")
    
    fixed = 0
    failed = 0
    missing = 0
    
    for filepath in CRITICAL_FILES:
        full_path = Path(filepath)
        
        if not full_path.exists():
            print(f"❌ Missing: {filepath}")
            missing += 1
            continue
            
        try:
            # First check if it has syntax errors
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                ast.parse(content)
            print(f"✅ Already valid: {filepath}")
            fixed += 1
        except SyntaxError as e:
            print(f"🔧 Fixing: {filepath} (Line {e.lineno}: {e.msg})")
            if fix_indentation_errors(full_path):
                print(f"✅ Fixed: {filepath}")
                fixed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error checking {filepath}: {e}")
            failed += 1
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Valid/Fixed: {fixed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ❓ Missing: {missing}")
    
    if failed > 0 or missing > 0:
        print("\n⚠️  Some critical files need manual attention!")
        return 1
    else:
        print("\n✅ All critical files are ready!")
        return 0

if __name__ == "__main__":
    exit(main())