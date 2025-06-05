import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Clean up corrupted backup files and deadend files to avoid confusion
"""

import os
import json
from pathlib import Path
from typing import List, Tuple

def identify_cleanup_candidates() -> Tuple[List[str], List[str]]:
    """Identify files that should be deleted vs archived"""
    to_delete = []
    to_check = []
    
    # Patterns for files to delete
    delete_patterns = [
        '*.corrupted_backup',
        '*.corrupted_archive',
        '*.corrupted',
        '*.backup',
        '*.restored'  # If restoration was successful, we don't need these
    ]
    
    # Find all matching files
    for pattern in delete_patterns:
        for file in Path('.').rglob(pattern):
            to_delete.append(str(file))
    
    # Check for specific deadend files from our analysis
    # These are files that were identified as severely corrupted with no restoration path
    with open('methodical_restoration_report.json', 'r') as f:
        report = json.load(f)
    
    # Files that couldn't be restored and have no value
    for analysis in report['analyses']:
        if (analysis['risk_level'] == 'critical' and 
            analysis['restoration_feasibility'] < 0.3 and
            'archive_and_rewrite' in analysis['recommended_approach']):
            to_check.append(analysis['file'])
    
    return to_delete, to_check

def cleanup_files(to_delete: List[str], to_check: List[str]):
    """Delete identified files and report actions"""
    deleted = []
    errors = []
    
    print("🧹 CLEANING UP CORRUPTED AND BACKUP FILES")
    print("=" * 80)
    
    # Delete backup files
    if to_delete:
        print(f"\n📁 Deleting {len(to_delete)} backup/corrupted files:")
        for file in to_delete:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    deleted.append(file)
                    print(f"  ✅ Deleted: {file}")
            except Exception as e:
                errors.append((file, str(e)))
                print(f"  ❌ Error deleting {file}: {e}")
    
    # Report on files to manually check
    if to_check:
        print(f"\n⚠️  Files requiring manual decision (severely corrupted):")
        for file in to_check:
            if os.path.exists(file):
                print(f"  - {file}")
                # Check if there's a working version from VCS
                try:
                    result = os.popen(f'git log -1 --oneline -- {file}').read().strip()
                    if result:
                        print(f"    → Has git history: {result}")
                    else:
                        print(f"    → No git history - consider deletion")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    pass
    
    # Summary
    print(f"\n{'=' * 80}")
    print("CLEANUP SUMMARY:")
    print(f"  Files deleted: {len(deleted)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Files to review: {len(to_check)}")
    
    # Save cleanup log
    cleanup_log = {
        'deleted_files': deleted,
        'errors': errors,
        'manual_review_needed': to_check
    }
    
    with open('cleanup_log.json', 'w') as f:
        json.dump(cleanup_log, f, indent=2)
    
    print(f"\n📄 Cleanup log saved: cleanup_log.json")

def main():
    """Execute cleanup with careful consideration"""
    to_delete, to_check = identify_cleanup_candidates()
    
    if not to_delete and not to_check:
        print("✅ No cleanup needed - workspace is clean!")
        return
    
    cleanup_files(to_delete, to_check)
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. Review files marked for manual decision")
    print("2. Delete files with no git history and no restoration path")
    print("3. Keep only files that can be restored or have reference value")
    print("4. Run 'git status' to see any untracked corrupted files")

if __name__ == "__main__":
    main()