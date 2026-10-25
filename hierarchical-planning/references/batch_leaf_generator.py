#!/usr/bin/env python3
"""
Batch leaf generator for hierarchical planning sessions.

Usage:
    python3 scripts/batch_leaf_generator.py plans-godot/

Creates leaf documents from a structured data definition. Useful when a plan
tree has many leaves (10+) and writing them individually is tedious.

The script reads leaf definitions from a Python list and generates .md files
with consistent structure: DISPATCH INSTRUCTION header, goal, tasks,
self-verification checklist, and review checklist.

Edit the `all_leaves` list in this script to define your leaves, then run it.
Each leaf definition is a tuple of:
    (branch, num, name, scope, deps, context, files_list, goal, tasks_list, checklist_items, review_items)

After generation, run the compliance scanner to verify all leaves are valid.
"""

import os
import sys

def create_leaf(base_dir, branch, num, name, scope, deps, context, files_list, goal, tasks_list, checklist_items, review_items):
    """Create a leaf document with standard hierarchical-planning structure."""
    
    files = "\n".join([f"- `{f}`" for f in files_list])
    task_sections = "\n\n".join([f"### Task {i+1}: {t['title']}\n\n{t['desc']}" for i, t in enumerate(tasks_list)])
    checklist = "\n".join([f"- [ ] {item}" for item in checklist_items])
    review = "\n".join([f"- [ ] {item}" for item in review_items])
    
    content = f"""# Leaf {num}: {name}

**DISPATCH INSTRUCTION**: Implement all tasks below. Do NOT commit. Do NOT run git add. Write code, run tests, report results only.

**Parent**: `plans-godot/{branch}/orchestrator.md`  
**Scope**: {scope}  
**Dependencies**: {deps}  
**Estimated Context**: ~{context}K  
**Files to Touch**: 
{files}

---

## Goal

{goal}

## Tasks

{task_sections}

## Self-Verification Checklist

After completing tasks:

{checklist}

## Review Checklist (for orchestrator)

When reviewing this leaf's output:

{review}

**Do NOT commit.** Report results only.
"""
    
    path = os.path.join(base_dir, branch, f"{num}-{name}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        f.write(content)
    
    return path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_leaf_generator.py <plans-dir>")
        print("Example: python3 batch_leaf_generator.py plans-godot/")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    
    # Define your leaves here — edit this list for your specific plan tree
    all_leaves = [
        # Example leaf definition:
        # ("branch-name", "01", "leaf-name", "scope description", "dependencies", "30",
        #  ["path/to/file1.gd", "path/to/file2.tscn"],
        #  "Goal statement",
        #  [{"title": "Task 1", "desc": "Description"}, {"title": "Task 2", "desc": "Description"}],
        #  ["Checklist item 1", "Checklist item 2"],
        #  ["Review item 1", "Review item 2"]),
        
        # Add your leaf definitions here
    ]
    
    created_count = 0
    for leaf_data in all_leaves:
        try:
            path = create_leaf(base_dir, *leaf_data)
            created_count += 1
            print(f"✓ Created: {os.path.basename(path)}")
        except Exception as e:
            print(f"✗ Failed: {leaf_data[1]}-{leaf_data[2]} — {e}")
    
    print(f"\nTotal leaves created: {created_count}")
    print("\nNext: Run compliance scan:")
    print(f"  python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py {base_dir} --strict-leaves")

if __name__ == "__main__":
    main()
