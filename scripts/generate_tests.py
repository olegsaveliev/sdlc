import os
import openai

# 1. SETUP
client = openai.OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# 2. READ THE CODE
with open("main.py", "r") as f:
    code_content = f.read()

# 3. ASK AI TO GENERATE TESTS
print("🤖 AI QA is analyzing code to generate regression tests...")
prompt = f"""
You are a QA Automation Engineer.
Here is the FastAPI code:
{code_content}

Task: Write a complete Python test file using 'pytest' and 'TestClient'.
Requirements:
1. Generate exactly 5 distinct test cases (Success, Failure, Edge cases).
2. The output must be ONLY python code, no markdown, no comments.
3. Name the functions test_ai_generated_1, test_ai_generated_2, etc.
"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

test_code = response.choices[0].message.content

# Clean up any markdown formatting if GPT added it
test_code = test_code.replace("```python", "").replace("```", "")

# 4. SAVE THE TESTS
with open("test_ai_generated.py", "w") as f:
    f.write(test_code)

print("✅ Generated 'test_ai_generated.py' with 5 new tests.")
