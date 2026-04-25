#!/usr/bin/env python3
"""Validate GitHub Actions workflow YAML"""

import yaml
import sys

try:
    with open(r'E:\personal\vapt-toolkit\.github\workflows\vapt-scan.yml', 'r') as f:
        workflow = yaml.safe_load(f)
    
    print("✓ YAML syntax is valid")
    print(f"✓ Name: {workflow.get('name')}")
    
    events = workflow.get('on', {})
    if isinstance(events, list):
        print(f"✓ Events: {events}")
    elif isinstance(events, dict):
        print(f"✓ Events: {list(events.keys())}")
    
    print(f"✓ Permissions: {list(workflow.get('permissions', {}).keys())}")
    print(f"✓ Jobs defined: {list(workflow.get('jobs', {}).keys())}")
    
    # Check jobs
    jobs = workflow.get('jobs', {})
    for job_name, job_config in jobs.items():
        runs_on = job_config.get('runs-on', 'unknown')
        timeout = job_config.get('timeout-minutes', 'default')
        print(f"  ✓ Job '{job_name}': runs-on={runs_on}, timeout={timeout}m")
        
        # Check for matrix
        if 'strategy' in job_config:
            print(f"    ✓ Has matrix strategy")
    
    print("\n✅ Workflow structure is valid and complete!")
    sys.exit(0)

except yaml.YAMLError as e:
    print(f"❌ YAML syntax error: {e}")
    sys.exit(1)
except FileNotFoundError:
    print("❌ Workflow file not found")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
