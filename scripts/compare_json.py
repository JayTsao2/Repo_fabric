#!/usr/bin/env python3
"""
JSON Comparison Tool
Compares two JSON files and shows the differences between them.
"""

import json
import sys
import os
from typing import Dict, Any, Tuple, List

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{filepath}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        sys.exit(1)

def compare_nvpairs(data1: Dict[str, Any], data2: Dict[str, Any]) -> Tuple[Dict, Dict, Dict]:
    """
    Compare nvPairs sections of two JSON objects.
    Returns: (only_in_first, only_in_second, different_values)
    """
    nvpairs1 = data1.get("nvPairs", {})
    nvpairs2 = data2.get("nvPairs", {})
    
    # Keys only in first file
    only_in_first = {k: v for k, v in nvpairs1.items() if k not in nvpairs2}
    
    # Keys only in second file
    only_in_second = {k: v for k, v in nvpairs2.items() if k not in nvpairs1}
    
    # Keys with different values
    different_values = {}
    for key in nvpairs1:
        if key in nvpairs2 and nvpairs1[key] != nvpairs2[key]:
            different_values[key] = {
                'file1': nvpairs1[key],
                'file2': nvpairs2[key]
            }
    
    return only_in_first, only_in_second, different_values

def print_comparison_report(file1_path: str, file2_path: str, 
                          only_in_first: Dict, only_in_second: Dict, 
                          different_values: Dict):
    """Print a formatted comparison report."""
    
    print("=" * 80)
    print(f"JSON COMPARISON REPORT")
    print("=" * 80)
    print(f"File 1: {file1_path}")
    print(f"File 2: {file2_path}")
    print("=" * 80)
    
    # Keys only in first file
    if only_in_first:
        print(f"\n🔴 KEYS ONLY IN FILE 1 ({len(only_in_first)} items):")
        print("-" * 50)
        for key, value in sorted(only_in_first.items()):
            print(f"  {key}: {repr(value)}")
    else:
        print(f"\n✅ No keys found only in File 1")
    
    # Keys only in second file
    if only_in_second:
        print(f"\n🔵 KEYS ONLY IN FILE 2 ({len(only_in_second)} items):")
        print("-" * 50)
        for key, value in sorted(only_in_second.items()):
            print(f"  {key}: {repr(value)}")
    else:
        print(f"\n✅ No keys found only in File 2")
    
    # Different values
    if different_values:
        print(f"\n🟡 DIFFERENT VALUES ({len(different_values)} items):")
        print("-" * 50)
        for key, values in sorted(different_values.items()):
            print(f"  {key}:")
            print(f"    File 1: {repr(values['file1'])}")
            print(f"    File 2: {repr(values['file2'])}")
            print()
    else:
        print(f"\n✅ No different values found")
    
    # Summary
    total_differences = len(only_in_first) + len(only_in_second) + len(different_values)
    print("=" * 80)
    print(f"SUMMARY: {total_differences} total differences found")
    print("=" * 80)

def export_differences_to_json(only_in_first: Dict, only_in_second: Dict, 
                             different_values: Dict, output_file: str):
    """Export differences to a JSON file for further processing."""
    
    report = {
        "comparison_summary": {
            "only_in_first_count": len(only_in_first),
            "only_in_second_count": len(only_in_second),
            "different_values_count": len(different_values),
            "total_differences": len(only_in_first) + len(only_in_second) + len(different_values)
        },
        "only_in_first": only_in_first,
        "only_in_second": only_in_second,
        "different_values": different_values
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        print(f"\n📁 Detailed comparison exported to: {output_file}")
    except Exception as e:
        print(f"Error writing report file: {e}")

def main():
    """Main function to handle command line arguments and run comparison."""
    
    if len(sys.argv) < 3:
        print("Usage: python compare_json.py <file1.json> <file2.json> [output_report.json]")
        print("\nExample:")
        print("  python compare_json.py MSD-TEST.json temp_payload_MSD-3.json")
        print("  python compare_json.py MSD-TEST.json temp_payload_MSD-3.json comparison_report.json")
        sys.exit(1)
    
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load JSON files
    print("Loading JSON files...")
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)
    
    # Compare nvPairs sections
    only_in_first, only_in_second, different_values = compare_nvpairs(data1, data2)
    
    # Print comparison report
    print_comparison_report(file1_path, file2_path, only_in_first, only_in_second, different_values)
    
    # Export to JSON if requested
    if output_file:
        export_differences_to_json(only_in_first, only_in_second, different_values, output_file)

if __name__ == "__main__":
    main()
