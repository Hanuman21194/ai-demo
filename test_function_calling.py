from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re
import wikipedia

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- TOOLS IMPLEMENTATION ---------------- #

def search_wikipedia(query: str):
    try:
        page = wikipedia.page(query, auto_suggest=True)
        return {
            "title": page.title,
            "url": page.url,
            "summary": page.summary[:1800]
        }
    except Exception as e:
        return {"error": str(e)}

def calculate(expression: str):
    if not re.match(r'^[0-9+\-*/().\s^]+$', expression):
        return {"error": "Invalid characters in expression"}

    try:
        expression = expression.replace("^", "**")
        result = eval(expression, {"__builtins__": {}})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}

def call_function(name: str, args: dict):
    if name == "search_wikipedia":
        return search_wikipedia(**args)
    if name == "calculate":
        return calculate(**args)
    raise ValueError(f"Unknown tool: {name}")

# ---------------- TOOL DEFINITIONS ---------------- #

CALCULATOR_TOOL = {
    "type": "function",
    "name": "calculate",
    "description": "Evaluate a mathematical expression",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"],
        "additionalProperties": False
    },
    "strict": True
}

WIKI_TOOL = {
    "type": "function",
    "name": "search_wikipedia",
    "description": "Fetch summary information from Wikipedia",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"],
        "additionalProperties": False
    },
    "strict": True
}

WEB_SEARCH = {"type": "web_search"}

TOOLS = [WIKI_TOOL, CALCULATOR_TOOL,WEB_SEARCH]

# ---------------- AGENT FUNCTION ---------------- #

def tool_calling(user_input: str, model="gpt-4o"):
    input_list = [{"role": "user", "content": user_input}]

    response = client.responses.create(
        model=model,
        input=input_list,
        tools=TOOLS,
        tool_choice="auto"
    )

    input_list.extend(response.output)

    tool_called = False

    for item in response.output:
        # Function tools → YOU execute
        if item.type == "function_call":
            tool_called = True
            args = json.loads(item.arguments)
            result = call_function(item.name, args)

            input_list.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result, ensure_ascii=False)
            })

    # Second call ONLY if function tools were used
    if tool_called:
        final_response = client.responses.create(
            model=model,
            instructions=(
                "Use the tool results and web search knowledge "
                "to give a clear, up-to-date answer. Use Markdown."
            ),
            input=input_list
        )
        return final_response.output_text

    # Otherwise, web_search or model-only answer
    return response.output_text    

# ---------------- TEST ---------------- #

if __name__ == "__main__":
    prompt = "What is value of 2+5+6+2-4 and who is Jagan Mohan Reddy? and today gold rate in vijayawada"
    print(tool_calling(prompt))
