#!/usr/bin/env python3
import pandas as pd
import sys
from io import StringIO
from .config import DATA_DIR


def validate_employees():
    # if len(sys.argv) < 2:
    #     print("Usage: python3 analyze_csv_full.py <file_path>")
    #     sys.exit(1)

    # file_path = sys.argv[1]
    file_path = DATA_DIR / "employees_clean.csv"


    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}\n")

    # First pass: count fields in each line to find structural issues
    print("=" * 80)
    print("FIELD COUNT ANALYSIS")
    print("=" * 80)

    field_counts = {}
    problematic_field_count_lines = []

    for idx in range(1, len(lines) - 1):  # Skip header (0) and footer (last)
        line = lines[idx].rstrip('\n\r')
        # Count unescaped pipes
        field_count = 0
        in_escape = False
        for char in line:
            if char == '\\':
                in_escape = True
            elif char == '|' and not in_escape:
                field_count += 1
            else:
                in_escape = False
        field_count += 1  # Account for final field

        if field_count not in field_counts:
            field_counts[field_count] = []
        field_counts[field_count].append(idx + 1)  # Line numbers (1-indexed)

        # Report if different from first line
        if idx == 1:
            expected_fields = field_count
        elif field_count != expected_fields:
            problematic_field_count_lines.append({
                'line_num': idx + 1,
                'expected': expected_fields,
                'actual': field_count,
                'diff': field_count - expected_fields,
                'content': line[:150]
            })

    print(f"\nExpected field count (from line 2): {expected_fields}")
    print(f"\nField count distribution:")
    for count in sorted(field_counts.keys()):
        num_lines = len(field_counts[count])
        if count == expected_fields:
            print(f"  {count} fields: {num_lines} lines ✓")
        else:
            print(f"  {count} fields: {num_lines} lines ❌ (diff: {count - expected_fields:+d})")

    if problematic_field_count_lines:
        print(f"\n❌ LINES WITH WRONG FIELD COUNT ({len(problematic_field_count_lines)} total):")
        for item in problematic_field_count_lines[:20]:  # Show first 20
            print(f"\n  Line {item['line_num']}: {item['actual']} fields (expected {item['expected']}, diff {item['diff']:+d})")
            print(f"    Preview: {repr(item['content'])}...")

        if len(problematic_field_count_lines) > 20:
            print(f"\n  ... and {len(problematic_field_count_lines) - 20} more lines with wrong field count")

    # Second pass: try to actually parse the file and catch parser errors
    print("\n" + "=" * 80)
    print("PANDAS PARSER VALIDATION")
    print("=" * 80)

    try:
        df = pd.read_csv(
            file_path,
            sep="|",
            escapechar="\\",
            header=None,
            skiprows=1,
            skipfooter=1,
            dtype=str,
            date_format="%Y%m%d",
            na_values=["null", "", " ", "  ", "   "],
            keep_default_na=False,
            engine="python"
        )
        print("\n✓ File parsed successfully!")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
    except Exception as e:
        print(f"\n❌ Parser failed: {type(e).__name__}")
        print(f"   {e}")

        # Try to extract line number from error if available
        error_str = str(e)
        if "line" in error_str.lower():
            print(f"   Details: {error_str}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if problematic_field_count_lines:
        print(f"⚠️  Found {len(problematic_field_count_lines)} lines with field count issues")
        print(f"   These lines need to be fixed in the source file")
    else:
        print(f"✓ All lines have correct field count")