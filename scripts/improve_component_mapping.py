#!/usr/bin/env python3
"""
Component Mapping Improvement Tool

This script analyzes the mappings between component-adaptation-mapping.json
and the implementation files (JS and Android) to identify and fix naming inconsistencies.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import csv

def load_json_file(file_path: str) -> Dict:
    """Load a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return {}

def load_text_file(file_path: str) -> str:
    """Load a text file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"Error loading file {file_path}: {e}")
        return ""

def get_normalized_names(component_name: str) -> List[str]:
    """Get normalized variations of a component name."""
    # Extract the base component name (e.g., "Button" from "Button (Primary)")
    base_name = component_name.split(' ')[0]
    
    # Generate different case variations
    camel_case = base_name[0].lower() + base_name[1:]  # e.g., "button"
    pascal_case = base_name  # e.g., "Button"
    kebab_case = re.sub(r'(?<!^)(?=[A-Z])', '-', base_name).lower()  # e.g., "button"
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', base_name).lower()  # e.g., "button"
    
    # Get any variant information (e.g., "Primary" from "Button (Primary)")
    variant = None
    if '(' in component_name and ')' in component_name:
        variant_match = re.search(r'\((.*?)\)', component_name)
        if variant_match:
            variant = variant_match.group(1)
    
    # Generate variants with the variant name
    variants = [base_name, camel_case, pascal_case, kebab_case, snake_case]
    
    if variant:
        # Convert variant to different cases
        variant_camel = variant[0].lower() + variant[1:] if len(variant) > 1 else variant.lower()
        variant_pascal = variant
        variant_kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', variant).lower()
        variant_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', variant).lower()
        
        # Add combinations
        variants.extend([
            f"{base_name}.{variant}",
            f"{base_name}.{variant_camel}",
            f"{base_name}.{variant_pascal}",
            f"{base_name}.{variant_kebab}",
            f"{base_name}.{variant_snake}",
            f"{camel_case}.{variant_camel}",
            f"{pascal_case}.{variant_pascal}",
            f"{kebab_case}-{variant_kebab}",
            f"{snake_case}_{variant_snake}",
            f"{base_name}{variant_pascal}",
            f"{camel_case}{variant_pascal}",
            # Add Android-style naming patterns
            f"{pascal_case}.{variant_pascal}",
            f"Orchestra.{pascal_case}.{variant_pascal}"
        ])
    
    return variants

def analyze_component_mapping(
    mapping_file: str,
    js_file: str,
    android_file: str,
    output_file: Optional[str] = None
) -> Dict:
    """
    Analyze the component mapping between JSON definition and implementation files.
    
    Args:
        mapping_file: Path to component-adaptation-mapping.json
        js_file: Path to JS implementation file (variables.js)
        android_file: Path to Android implementation file (styles.xml)
        output_file: Optional path to save detailed mapping results
        
    Returns:
        Dict containing analysis results
    """
    # Load files
    mapping_data = load_json_file(mapping_file)
    js_content = load_text_file(js_file)
    android_content = load_text_file(android_file)
    
    if not mapping_data or not js_content or not android_content:
        print("❌ Error loading required files")
        return {}
    
    # Results container
    results = {
        "total_components": len(mapping_data),
        "found_in_js": 0,
        "found_in_android": 0,
        "found_in_both": 0,
        "not_found": 0,
        "component_results": [],
        "js_patterns_found": set(),
        "android_patterns_found": set(),
    }
    
    # Pattern for finding component styles in Android XML
    android_patterns = [
        r'style name="([^"]+)"',  # Regular style definitions
        r'style name="Orchestra\.([^"]+)"',  # Orchestra prefixed styles
        r'name="([^"]+)"'  # Other named elements
    ]
    
    # Process each component
    for component_name in mapping_data.keys():
        component_result = {
            "name": component_name,
            "found_in_js": False,
            "found_in_android": False,
            "js_matches": [],
            "android_matches": [],
            "normalized_names": []
        }
        
        # Get all normalized name variations
        normalized_names = get_normalized_names(component_name)
        component_result["normalized_names"] = normalized_names
        
        # Check in JS file
        for pattern in normalized_names:
            if pattern in js_content:
                component_result["found_in_js"] = True
                component_result["js_matches"].append(pattern)
                results["js_patterns_found"].add(pattern)
        
        # Check in Android file
        for pattern in normalized_names:
            if pattern in android_content:
                component_result["found_in_android"] = True
                component_result["android_matches"].append(pattern)
                results["android_patterns_found"].add(pattern)
        
        # Additional specific checks for Android styles
        for android_pattern in android_patterns:
            matches = re.findall(android_pattern, android_content)
            for match in matches:
                for name in normalized_names:
                    if name in match:
                        component_result["found_in_android"] = True
                        component_result["android_matches"].append(match)
                        results["android_patterns_found"].add(match)
        
        # Update summary counts
        if component_result["found_in_js"]:
            results["found_in_js"] += 1
        
        if component_result["found_in_android"]:
            results["found_in_android"] += 1
        
        if component_result["found_in_js"] and component_result["found_in_android"]:
            results["found_in_both"] += 1
        
        if not component_result["found_in_js"] and not component_result["found_in_android"]:
            results["not_found"] += 1
        
        results["component_results"].append(component_result)
    
    # Save detailed results if output file specified
    if output_file:
        save_detailed_results(results, output_file)
    
    return results

def save_detailed_results(results: Dict, output_file: str) -> None:
    """Save detailed analysis results to a CSV file."""
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "Component Name", 
                "Found in JS", 
                "Found in Android", 
                "JS Matches", 
                "Android Matches"
            ])
            
            # Write component results
            for comp in results["component_results"]:
                writer.writerow([
                    comp["name"],
                    comp["found_in_js"],
                    comp["found_in_android"],
                    ", ".join(comp["js_matches"]) if comp["js_matches"] else "None",
                    ", ".join(comp["android_matches"]) if comp["android_matches"] else "None"
                ])
            
            # Write summary
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Components", results["total_components"]])
            writer.writerow(["Found in JS", results["found_in_js"]])
            writer.writerow(["Found in Android", results["found_in_android"]])
            writer.writerow(["Found in Both", results["found_in_both"]])
            writer.writerow(["Not Found", results["not_found"]])
            
            # Write pattern information
            writer.writerow([])
            writer.writerow(["JS Patterns Found"])
            for pattern in sorted(results["js_patterns_found"]):
                writer.writerow([pattern])
                
            writer.writerow([])
            writer.writerow(["Android Patterns Found"])
            for pattern in sorted(results["android_patterns_found"]):
                writer.writerow([pattern])
                
        print(f"✅ Detailed results saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving detailed results: {e}")

def generate_mapping_recommendations(results: Dict) -> Dict:
    """Generate recommendations for improving component mappings."""
    recommendations = {
        "rename_suggestions": [],
        "implementation_suggestions": []
    }
    
    # Analyze patterns that were successfully matched
    successful_js_patterns = sorted(results["js_patterns_found"])
    successful_android_patterns = sorted(results["android_patterns_found"])
    
    # Generate rename suggestions
    for comp in results["component_results"]:
        if not comp["found_in_js"] and not comp["found_in_android"]:
            base_name = comp["name"].split(' ')[0]
            
            # Try to find similar components that were successfully matched
            similar_js = [p for p in successful_js_patterns if base_name.lower() in p.lower()]
            similar_android = [p for p in successful_android_patterns if base_name.lower() in p.lower()]
            
            if similar_js or similar_android:
                recommendations["rename_suggestions"].append({
                    "component": comp["name"],
                    "suggestion": (
                        f"Consider renaming to match existing patterns: "
                        f"JS: {', '.join(similar_js[:3])} | "
                        f"Android: {', '.join(similar_android[:3])}"
                    )
                })
            else:
                recommendations["rename_suggestions"].append({
                    "component": comp["name"],
                    "suggestion": "No similar patterns found. Consider following project conventions for naming."
                })
    
    # Generate implementation suggestions
    for comp in results["component_results"]:
        if comp["found_in_js"] and not comp["found_in_android"]:
            recommendations["implementation_suggestions"].append({
                "component": comp["name"],
                "suggestion": f"Implement in Android using pattern from JS: {', '.join(comp['js_matches'][:3])}"
            })
        elif comp["found_in_android"] and not comp["found_in_js"]:
            recommendations["implementation_suggestions"].append({
                "component": comp["name"],
                "suggestion": f"Implement in JS using pattern from Android: {', '.join(comp['android_matches'][:3])}"
            })
    
    return recommendations

def print_analysis_results(results: Dict, recommendations: Dict) -> None:
    """Print analysis results and recommendations."""
    print("\n=== COMPONENT MAPPING ANALYSIS ===")
    print(f"Total components defined: {results['total_components']}")
    print(f"Found in JS: {results['found_in_js']} ({results['found_in_js']/results['total_components']*100:.1f}%)")
    print(f"Found in Android: {results['found_in_android']} ({results['found_in_android']/results['total_components']*100:.1f}%)")
    print(f"Found in both: {results['found_in_both']} ({results['found_in_both']/results['total_components']*100:.1f}%)")
    print(f"Not found: {results['not_found']} ({results['not_found']/results['total_components']*100:.1f}%)")
    
    # Print components not found
    if results["not_found"] > 0:
        print("\nComponents not found in any implementation:")
        for comp in results["component_results"]:
            if not comp["found_in_js"] and not comp["found_in_android"]:
                print(f"  • {comp['name']}")
    
    # Print recommendations
    if recommendations["rename_suggestions"]:
        print("\n=== RENAME RECOMMENDATIONS ===")
        for rec in recommendations["rename_suggestions"]:
            print(f"• {rec['component']}:")
            print(f"  {rec['suggestion']}")
    
    if recommendations["implementation_suggestions"]:
        print("\n=== IMPLEMENTATION RECOMMENDATIONS ===")
        for rec in recommendations["implementation_suggestions"]:
            print(f"• {rec['component']}:")
            print(f"  {rec['suggestion']}")

def main():
    parser = argparse.ArgumentParser(description='Analyze component mappings between definitions and implementations')
    parser.add_argument('--mapping', default='component-adaptation-mapping.json',
                        help='Path to component-adaptation-mapping.json')
    parser.add_argument('--js', default='packages/ui/src/tokens/variables.js',
                        help='Path to JavaScript implementation file')
    parser.add_argument('--android', default='packages/ui/android/src/main/res/values/styles.xml',
                        help='Path to Android implementation file')
    parser.add_argument('--output', default='component_mapping_analysis.csv',
                        help='Path to save detailed mapping results')
    
    args = parser.parse_args()
    
    print(f"Analyzing component mappings...")
    print(f"• Mapping file: {args.mapping}")
    print(f"• JS file: {args.js}")
    print(f"• Android file: {args.android}")
    
    # Run analysis
    results = analyze_component_mapping(args.mapping, args.js, args.android, args.output)
    
    if not results:
        print("❌ Analysis failed")
        return 1
    
    # Generate recommendations
    recommendations = generate_mapping_recommendations(results)
    
    # Print results and recommendations
    print_analysis_results(results, recommendations)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
