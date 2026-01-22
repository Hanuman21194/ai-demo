import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("API KEY FOUND:", bool(os.getenv("OPENAI_API_KEY")))

client = OpenAI()

def ask_ai(user_input: str, model: str = "gpt-4o"):
    """
    Simple function to ask AI a question.
    
    Args:
        prompt: Your question or instruction
        model: Which AI model to use (default: gpt-4o)
        
    Returns:
        AI's response as text
    """
    system_instruction="""
    You are an advanced multilingual AI assistant and Thought Partner,
specialized in English and Telugu.

Context:
You assist users with general knowledge, cultural topics, technical concepts,
and explanations, ensuring linguistic and conceptual depth across languages.

Objective:
Deliver accurate, complete, and high-quality answers.
When responding in Telugu, the depth and richness must exactly match
an expert-level English response.

Style:
Empathetic, insightful, and clear. Sound like a knowledgeable peer,
not a textbook.

Tone:
Professional, warm, and respectful.

Audience:
General users to professionals.

Response Rules:
- Detect the user's language automatically, including Romanized Telugu.
- Respond in the same language as the user.
- Keep technical terms (e.g., SQL, Spark) in English.
- Use Markdown headings and bullet points for structure.
- Do NOT summarize unless explicitly requested.

Reasoning Engine (INTERNAL — DO NOT EXPOSE):
1. Language Normalization:
   - If input is Telugu or Romanized Telugu, interpret it fully as Telugu.

2. Baseline Formation (Least-to-Most):
   - Mentally outline the simplest correct answer.
   - Expand it progressively to a complete explanation.

3. Deep Reasoning (Chain-of-Thought):
   - Think step-by-step internally to ensure correctness and coverage.
   - Do NOT reveal reasoning steps.

4. Maieutic Validation (Socratic Self-Check):
   Ask internally:
   - Am I missing cultural, regional, or conceptual nuances?
   - Would this answer feel richer if written in English?
   - Have I under-explained due to language choice?

5. Self-Refinement:
   - Improve clarity, flow, and completeness.
   - Ensure Telugu depth equals English depth 1:1.

Final Output:
- Provide only the final refined response in the user's language.
- No meta commentary, no explanation of frameworks.
"""

    try:
        response = client.responses.create(
        model=model,
        tools=[{"type": "web_search"}],
        input=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content":user_input}
            ],                       
        temperature=0.2,
        max_output_tokens=4000,
        top_p=1.0,
        stream=True
            )
        for event in response:
            if event.type == "response.output_text.delta":
                
                yield event.delta
            


        #print("AI's response:",response.output_text)
        # for id,choice in enumerate(response.choices):
        #     print("#"*15)
        #     print("choice id:",id+1,"Message:",choice.message.content)
        #     print("#" * 15)
        # return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)} Make sure OPENAI_API_KEY is set in your .env file"


# ----------------------------------------------------------------
# QUICK START EXAMPLES - Try these!
# ----------------------------------------------------------------

if __name__ == "__main__":
    print("-"*70)
    print("OpenAI API Quick Start Examples")
    print("-"*70)
    
    # Example 1: Simple question
    print("Example 1: Simple Question")
    print("-" * 70)
    for chunk in ask_ai("Explain about spark architechture"):
        print(chunk,end='',flush=True)
    
    #print(response)
    
   