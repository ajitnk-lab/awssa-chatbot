#!/usr/bin/env python3
"""
Convert classification_results_awslabs.csv to JSON documents for Bedrock Knowledge Base.
Creates enriched JSON documents with searchable content for semantic search.
"""

import csv
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_searchable_content(row):
    """Create enriched searchable content from repository data."""
    content_parts = [
        f"Repository: {row['repository']}",
        f"Description: {row['description']}",
        f"Solution Type: {row['solution_type']}",
        f"Primary Language: {row['primary_language']}",
        f"AWS Services: {row['aws_services']}",
        f"Technical Competencies: {row['technical_competencies']}",
        f"Solution Competencies: {row['solution_competencies']}",
        f"Deployment Tools: {row['deployment_tools']}",
        f"Setup Time: {row['setup_time']}",
        f"Cost Range: {row['cost_range']}",
        f"Customer Problems: {row['customer_problems']}",
        f"USP: {row['usp']}",
        f"Prerequisites: {row['prerequisites']}",
        f"License: {row['license']}"
    ]
    
    # Add additional languages if present
    if row['additional_languages'].strip():
        content_parts.append(f"Additional Languages: {row['additional_languages']}")
    
    # Add frameworks if present
    if row['frameworks'].strip():
        content_parts.append(f"Frameworks: {row['frameworks']}")
    
    return "\n".join(content_parts)

def convert_csv_to_json():
    """Convert CSV file to individual JSON documents."""
    csv_file = Path("classification_results_awslabs.csv")
    output_dir = Path("data/repos")
    
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return False
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Create repository identifier (safe filename)
                    repo_name = row['repository'].replace('/', '_')
                    filename = f"{repo_name}.json"
                    
                    # Create JSON document
                    document = {
                        "repository": row['repository'],
                        "url": row['url'],
                        "searchable_content": create_searchable_content(row),
                        "metadata": {
                            "description": row['description'],
                            "created_date": row['created_date'],
                            "last_modified": row['last_modified'],
                            "stars": int(row['stars']) if row['stars'].isdigit() else 0,
                            "forks": int(row['forks']) if row['forks'].isdigit() else 0,
                            "solution_type": row['solution_type'],
                            "solution_marketing": row['solution_marketing'],
                            "technical_competencies": row['technical_competencies'],
                            "solution_competencies": row['solution_competencies'],
                            "deployment_tools": row['deployment_tools'],
                            "deployment_level": row['deployment_level'],
                            "primary_language": row['primary_language'],
                            "additional_languages": row['additional_languages'],
                            "frameworks": row['frameworks'],
                            "aws_services": row['aws_services'],
                            "prerequisites": row['prerequisites'],
                            "license": row['license'],
                            "setup_time": row['setup_time'],
                            "cost_range": row['cost_range'],
                            "customer_problems": row['customer_problems'],
                            "usp": row['usp'],
                            "freshness_status": row['freshness_status']
                        }
                    }
                    
                    # Write JSON file
                    output_path = output_dir / filename
                    with open(output_path, 'w', encoding='utf-8') as json_file:
                        json.dump(document, json_file, indent=2, ensure_ascii=False)
                    
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count} repositories...")
                        
                except Exception as e:
                    logger.error(f"Error processing row {row.get('repository', 'unknown')}: {e}")
                    error_count += 1
                    continue
    
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return False
    
    logger.info(f"Conversion complete!")
    logger.info(f"Successfully processed: {processed_count} repositories")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    
    return processed_count > 0

if __name__ == "__main__":
    success = convert_csv_to_json()
    exit(0 if success else 1)
