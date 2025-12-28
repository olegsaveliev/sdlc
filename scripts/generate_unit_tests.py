import os
import openai

# 1. SETUP
client = openai.OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# 2. READ THE DEV'S CODE
try:
    with open("main.py", "r") as f:
        code_content = f.read()
except FileNotFoundError:
    print("❌ Could not find main.py. Exiting.")
    exit(1)

# 3. ASK AI TO WRITE UNIT TESTS
print("🧠 AI is reading your code to write Unit Tests...")
prompt = f"""
You are a Senior Python Developer.
Your Task: Write a 'pytest' file for the following code.
Code:
{code_content}

Rules:
1. Cover Success scenarios.
2. Cover Error scenarios (400/404/500).
3. Use 'TestClient' from fastapi.testclient.
4. Output ONLY raw python code. No markdown (```), no explanation.
"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

test_code = response.choices[0].message.content

# Clean up formatting if GPT adds backticks
test_code = test_code.replace("```python", "").replace("```", "")

# 4. SAVE THE FILE (Ephemeral - exists only during pipeline run)
with open("test_auto_generated.py", "w") as f:
    f.write(test_code)

print("✅ Created 'test_auto_generated.py' with fresh unit tests.")
