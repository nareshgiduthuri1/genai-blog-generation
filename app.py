import json
import boto3
import botocore.config
from datetime import datetime

def blog_generate_using_bedrock(blogtopic: str) -> str:

    prompt = f'''
    You are a blog writer. Write a blog on the topic {blogtopic} in 200 words.
    '''

    body  = {
        "schemaVersion": "messages-v1",
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ],
        "inferenceConfig": {
            "max_new_tokens": 600,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        client = boto3.client('bedrock-runtime', region_name = 'us-east-1',
                    config = botocore.config.Config(read_timeout=300, retries={'max_attempts': 3}) )
        response = client.invoke_model(body = json.dumps(body), modelId = 'amazon.nova-micro-v1:0')
        response_content = response.get('body').read()
        response_data = json.loads(response_content)
        print(response_data)
        blog_details = response_data['output']['message']['content'][0]['text']
        return blog_details

    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def upload_to_s3(bucket_name, bucket_key, blog):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=bucket_key, Body=blog)
        print(f"Successfully uploaded to S3: {bucket_name}/{bucket_key}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

def lambda_handler(event, context):
    
    try:
        event = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Request body must be valid JSON.'})
        }

    blogtopic = event.get('blogtopic')
    if not blogtopic:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'blogtopic is required.'})
        }

    blog = blog_generate_using_bedrock(blogtopic)

    if blog:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"blog_outputs/{current_time}.txt"
        s3_bucket = "genai-blog-generation"
        upload_to_s3(s3_bucket, s3_key, blog)
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate blog.'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps(blog)
    }