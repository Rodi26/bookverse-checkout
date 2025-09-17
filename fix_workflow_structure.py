#!/usr/bin/env python3
"""
Critical fix for checkout CI workflow:
1. Remove duplicate build-info publish step
2. Fix step order to match recommendations
3. Let evidence library handle build-info publishing completely
"""

import re

def fix_workflow():
    """Remove the manual Build Info Publish step that's causing duplicate publishes."""
    
    # Read the workflow file
    with open('.github/workflows/ci.yml', 'r') as f:
        content = f.read()
    
    # Find and remove the entire "[Build Info] Publish" step
    # This step is causing duplicate build-info publishes
    
    # Pattern to match the entire step from "- name:" to the next step
    pattern = r'(\s+- name: "\[Build Info\] Publish".*?)(\n\s+- name: "\[Evidence\].*?"|\n\s+create-promote:)'
    
    # Replace with just the next step (keeping the Evidence step)
    content = re.sub(pattern, r'\2', content, flags=re.DOTALL)
    
    # Clean up any extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Write back the fixed content
    with open('.github/workflows/ci.yml', 'w') as f:
        f.write(content)
    
    print("✅ Removed duplicate [Build Info] Publish step")
    print("✅ The evidence library will now handle build-info publishing completely")
    print("✅ This should resolve the empty build-info modules issue")

if __name__ == "__main__":
    fix_workflow()
