#!/usr/bin/env python3
"""
Basic Lambda function test without external dependencies
Tests the Lambda function structure and basic functionality
"""

import json
import sys
import os
from pathlib import Path

def test_lambda_structure():
    """Test the Lambda function file structure."""
    
    print("🧪 Testing Lambda function structure...")
    
    lambda_dir = Path('lambda')
    if not lambda_dir.exists():
        print("❌ Lambda directory not found!")
        return False
    
    required_files = [
        'lambda/lambda_function.py',
        'lambda/requirements.txt',
        'lambda/deploy.sh'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    if not all_exist:
        return False
    
    # Check Lambda function content
    lambda_file = Path('lambda/lambda_function.py')
    with open(lambda_file, 'r') as f:
        content = f.read()
    
    required_elements = [
        'lambda_handler',
        'SYSTEM_PROMPT',
        'bedrock_runtime',
        'strands_agents'
    ]
    
    for element in required_elements:
        if element in content:
            print(f"✅ Found {element} in Lambda function")
        else:
            print(f"❌ Missing {element} in Lambda function")
            all_exist = False
    
    return all_exist

def test_requirements():
    """Test requirements.txt content."""
    
    print("\n📦 Testing requirements.txt...")
    
    req_file = Path('lambda/requirements.txt')
    with open(req_file, 'r') as f:
        requirements = f.read()
    
    required_packages = [
        'strands-agents',
        'boto3',
        'botocore'
    ]
    
    all_found = True
    for package in required_packages:
        if package in requirements:
            print(f"✅ Found {package}")
        else:
            print(f"❌ Missing {package}")
            all_found = False
    
    return all_found

def test_environment_variables():
    """Test environment variable usage in Lambda function."""
    
    print("\n🔧 Testing environment variables...")
    
    lambda_file = Path('lambda/lambda_function.py')
    with open(lambda_file, 'r') as f:
        content = f.read()
    
    env_vars = [
        'KNOWLEDGE_BASE_ID',
        'MODEL_ID',
        'REGION'
    ]
    
    all_found = True
    for var in env_vars:
        if f"os.environ.get('{var}'" in content:
            print(f"✅ Environment variable {var} is used")
        else:
            print(f"❌ Environment variable {var} not found")
            all_found = False
    
    return all_found

def main():
    """Run basic Lambda tests."""
    
    print("🚀 AWS Solutions Architect Agent - Basic Lambda Testing")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test Lambda structure
    if test_lambda_structure():
        tests_passed += 1
    
    # Test requirements
    if test_requirements():
        tests_passed += 1
    
    # Test environment variables
    if test_environment_variables():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ Basic Lambda tests passed! Function structure is correct.")
        print("ℹ️  Note: Full functionality testing requires deployment to AWS.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
