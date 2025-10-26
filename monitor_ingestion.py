#!/usr/bin/env python3
import boto3
import time
import json

client = boto3.client('bedrock-agent', region_name='us-west-2')

def monitor_ingestion():
    kb_id = "TOJENJXGHW"
    ds_id = "NRTZFOH2YX" 
    job_id = "AMHZACFJFX"
    
    while True:
        try:
            response = client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            job = response['ingestionJob']
            stats = job['statistics']
            
            print(f"\n⏰ {time.strftime('%H:%M:%S')}")
            print(f"📊 Status: {job['status']}")
            print(f"✅ Indexed: {stats['numberOfNewDocumentsIndexed']}")
            print(f"❌ Failed: {stats['numberOfDocumentsFailed']}")
            print(f"📄 Scanned: {stats['numberOfDocumentsScanned']}")
            
            if stats['numberOfDocumentsFailed'] > 0:
                print(f"🔍 Success Rate: {(stats['numberOfNewDocumentsIndexed']/(stats['numberOfNewDocumentsIndexed']+stats['numberOfDocumentsFailed']))*100:.1f}%")
            
            if job['status'] in ['COMPLETE', 'FAILED']:
                print(f"\n🏁 Final Status: {job['status']}")
                if 'failureReasons' in job and job['failureReasons']:
                    print("❌ Failure Reasons:")
                    for reason in job['failureReasons'][:3]:  # Show first 3
                        print(f"   • {reason[:100]}...")
                break
                
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor_ingestion()
