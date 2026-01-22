import os
import boto3
from datetime import datetime, timezone
from typing import List, Dict, Any
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

load_dotenv()

class BedrockPromptManager:
    def __init__(self, region_name: str = "us-east-1", table_name: str = "PromptRegistry"):
        self.region = region_name
        # Clients
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.mapping_table = self.dynamodb.Table(table_name)

    def create_or_update_prompt(
        self,
        name: str,
        description: str,
        prompt_text: str,
        variables: List[str],
        model_id: str,
        temperature: float,
        max_tokens: int
    ):
        ts_key = datetime.now(timezone.utc).isoformat()
        prompt_id = None
        prompt_arn = None
        bedrock_version = "DRAFT"

        # 1. SYNC CHECK: Look in DynamoDB first, then Bedrock
        response = self.mapping_table.query(
            KeyConditionExpression=Key('prompt_name').eq(name),
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get('Items', [])

        if items:
            prompt_id = items[0]['prompt_id']
            print(f"🔎 Found ID in DynamoDB: {prompt_id}")
        else:
            print(f"🔍 Searching Bedrock for existing prompt: {name}...")
            all_prompts = self.bedrock_agent.list_prompts()
            for p in all_prompts.get('promptSummaries', []):
                if p['name'] == name:
                    prompt_id = p['id']
                    print(f"🔗 Linked existing Bedrock ID: {prompt_id}")
                    break

        # 2. PREPARE VARIANT CONFIG
        variant_config = {
            "name": "variant1",
            "templateType": "TEXT",
            "templateConfiguration": {
                "text": {
                    "text": prompt_text,
                    "inputVariables": [{"name": var} for var in variables]
                }
            },
            "modelId": model_id,
            "inferenceConfiguration": {
                "text": {
                    "temperature": temperature,
                    "maxTokens": max_tokens
                }
            }
        }

        # 3. EXECUTE BEDROCK OPERATIONS
        try:
            if not prompt_id:
                print(f"✨ Creating brand new prompt in Bedrock...")
                create_res = self.bedrock_agent.create_prompt(
                    name=name,
                    description=description,
                    variants=[variant_config]
                )
                prompt_id = create_res['id']
                prompt_arn = create_res['arn']
                bedrock_version = "1"
            else:
                print(f"🆙 Updating existing prompt...")
                update_res = self.bedrock_agent.update_prompt(
                    promptIdentifier=prompt_id,
                    name=name,
                    description=description,
                    variants=[variant_config]
                )
                prompt_arn = update_res['arn']
                
                # Create a version snapshot
                version_res = self.bedrock_agent.create_prompt_version(
                    promptIdentifier=prompt_id
                )
                bedrock_version = version_res.get('version', 'N/A')

            # 4. SAVE COMPREHENSIVE METADATA TO DYNAMODB
            full_item = {
                "prompt_name": name,           # Partition Key
                "timestamp": ts_key,           # Sort Key
                "version": bedrock_version,    # Bedrock internal version
                "prompt_id": prompt_id,
                "prompt_arn": prompt_arn,
                "model_id": model_id,
                "temperature": str(temperature),
                "max_tokens": max_tokens,
                "template": prompt_text,
                "updated_at": ts_key,
                "status": "ACTIVE",
                "description": description,
                "created_by": os.getlogin() if hasattr(os, 'getlogin') else "system",
                "checksum": str(hash(prompt_text))
            }

            self.mapping_table.put_item(Item=full_item)
            print(f"✅ Successfully registered {name} (v{bedrock_version}) at {ts_key}")
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    manager = BedrockPromptManager()
    
    # Run the update
    manager.create_or_update_prompt(
        name="sql_creation",
        description="Generates optimized ANSI SQL based on schema",
        prompt_text="You are a senior Data Engineer. Use ANSI SQL. \nSchema: {{schema}} \nQuestion: {{question}} \nOutput SQL only.",
        variables=["schema", "question"],
        model_id="us.amazon.nova-lite-v1:0",
        temperature=0.7,
        max_tokens=1000
    )