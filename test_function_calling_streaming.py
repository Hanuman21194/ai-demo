from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re
import wikipedia

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model =os.getenv("gpt_model")

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

def tool_calling(messages: list, model:str):
    #input_list = [{"role": "user", "content": messages}]

    response = client.responses.create(
        model=model,
        input=messages,
        tools=TOOLS,
        tool_choice="auto",
        stream=True
    )

    assistant_text = ""
    tool_calls = []

    for event in response:

        # Collect assistant text
        if event.type == "response.output_text.delta":
            assistant_text += event.delta
            yield event.delta
        # Tool call created
        elif event.type == "response.output_item.added":
            if event.item.type == "function_call":
                tool_calls.append({
                    "name": event.item.name,
                    "arguments": "",
                    "call_id": event.item.call_id
                })

        # Tool arguments streaming
        elif event.type == "response.function_call_arguments.delta":
            tool_calls[-1]["arguments"] += event.delta

        elif event.type == "response.completed":
            break

    # Add assistant text if present  this not for front end with API
    # if assistant_text.strip():
    #     input_list.append({
    #         "role": "assistant",
    #         "content": assistant_text
    #     })

    # Execute tools
    for tool in tool_calls:
        # 1️⃣ Echo assistant tool call
        messages.append({
            "type": "function_call",
            "name": tool["name"],
            "arguments": tool["arguments"],
            "call_id": tool["call_id"]
        })

        # 2️⃣ Execute tool
        args = json.loads(tool["arguments"])
        result = call_function(tool["name"], args)

        # 3️⃣ Send tool output
        messages.append({
            "type": "function_call_output",
            "call_id": tool["call_id"],
            "output": json.dumps(result, ensure_ascii=False)
        })


    # Ask model for final answer if tools were used
    if tool_calls:
        final_response = client.responses.create(
            model=model,
            instructions=(
                "Use all available information (tool results and web search knowledge) "
                "to give a clear, comprehensive, well-formatted answer."
            ),
            input=messages,
            stream=True
        )
        for event in final_response:
            if event.type == "response.output_text.delta":
                yield event.delta
        # this is for non streaming return final_response.output_text

    return assistant_text or "No response generated."


    
if __name__ == "__main__":
    prompt = "What is value of 2+5+6+2-4 and who is Jagan Mohan Reddy? and today gold rate in vijayawada"
    print(tool_calling(prompt))
