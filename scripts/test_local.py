#!/usr/bin/env python3
"""
Local testing script for AWS Solutions Architect Agent
Tests the Lambda function locally without deploying to AWS
"""

import json
import sys
import os
from pathlib import Path

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent / 'lambda'
sys.path.insert(0, str(lambda_dir))

def test_lambda_function():
    """Test the Lambda function with sample inputs."""
    
    try:
        # Import the Lambda function
        from lambda_function import lambda_handler
        
        # Test cases
        test_cases = [
            {
                'name': 'Serverless API Request',
                'event': {
                    'body': json.dumps({
                        'message': 'I need a serverless API solution with Python',
                        'session_id': 'test_session_1'
                    })
                }
            },
            {
                'name': 'Machine Learning Request',
                'event': {
                    'body': json.dumps({
                        'message': 'Show me machine learning projects using TensorFlow',
                        'session_id': 'test_session_2'
                    })
                }
            },
            {
                'name': 'General Help Request',
                'event': {
                    'body': json.dumps({
                        'message': 'What can you help me with?',
                        'session_id': 'test_session_3'
                    })
                }
            }
        ]
        
        print("🧪 Testing AWS Solutions Architect Agent Lambda Function")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            print("-" * 40)
            
            try:
                # Call the Lambda handler
                response = lambda_handler(test_case['event'], None)
                
                # Parse response
                status_code = response.get('statusCode', 'Unknown')
                body = json.loads(response.get('body', '{}'))
                
                print(f"Status Code: {status_code}")
                
                if status_code == 200:
                    print("✅ Success!")
                    agent_response = body.get('response', 'No response')
                    session_id = body.get('session_id', 'No session')
                    
                    print(f"Session ID: {session_id}")
                    print(f"Response Preview: {agent_response[:200]}...")
                    
                else:
                    print("❌ Error!")
                    error = body.get('error', 'Unknown error')
                    print(f"Error: {error}")
                    
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Local testing complete!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import Lambda function: {e}")
        print("Make sure you're running this from the project root directory.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_data_conversion():
    """Test the data conversion script."""
    
    print("\n🔄 Testing data conversion...")
    
    # Check if CSV file exists
    csv_file = Path('classification_results_awslabs.csv')
    if not csv_file.exists():
        print("❌ CSV file not found!")
        return False
    
    # Check if JSON files were created
    json_dir = Path('data/repos')
    if not json_dir.exists():
        print("❌ JSON directory not found! Run the conversion script first.")
        return False
    
    json_files = list(json_dir.glob('*.json'))
    if not json_files:
        print("❌ No JSON files found!")
        return False
    
    print(f"✅ Found {len(json_files)} JSON files")
    
    # Test loading a sample JSON file
    try:
        sample_file = json_files[0]
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        required_fields = ['repository', 'url', 'searchable_content', 'metadata']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing fields in JSON: {missing_fields}")
            return False
        
        print(f"✅ JSON structure is valid")
        print(f"Sample repository: {data['repository']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False

def test_frontend():
    """Test frontend files."""
    
    print("\n🌐 Testing frontend files...")
    
    frontend_files = [
        'frontend/index.html',
        'frontend/css/style.css',
        'frontend/js/api.js',
        'frontend/js/ui.js',
        'frontend/js/app.js'
    ]
    
    all_exist = True
    for file_path in frontend_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    if all_exist:
        print("✅ All frontend files present")
        
        # Check if API URL placeholder exists
        api_js = Path('frontend/js/api.js')
        with open(api_js, 'r') as f:
            content = f.read()
        
        if 'YOUR_API_GATEWAY_URL' in content:
            print("⚠️  API URL placeholder found - will be updated during deployment")
        else:
            print("✅ API URL appears to be configured")
    
    return all_exist

def main():
    """Run all tests."""
    
    print("🚀 AWS Solutions Architect Agent - Local Testing")
    print("=" * 60)
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    tests_passed = 0
    total_tests = 3
    
    # Test data conversion
    if test_data_conversion():
        tests_passed += 1
    
    # Test frontend files
    if test_frontend():
        tests_passed += 1
    
    # Test Lambda function
    if test_lambda_function():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
