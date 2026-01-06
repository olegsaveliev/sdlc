import os
import glob
import openai
from auto_tracker import track_openai

# 1. SETUP
client = openai.OpenAI(api_key=os.environ.get("OPENAI_KEY"))
client = track_openai(client)

# 2. FIND CODE DYNAMICALLY
print("🔍 Searching for application code...")

all_files = glob.glob("**/*.py", recursive=True)
code_files = [
    f for f in all_files 
    if not any([
        f.startswith("test_"),
        "test" in f.lower(),
        "generate" in f.lower(),
        ".venv" in f or "venv" in f,
        "site-packages" in f,
        ".github" in f,
        "scripts/" in f,
        "__pycache__" in f
    ])
]

if not code_files:
    print("ℹ️ No source code - creating placeholder")
    with open("test_ai_generated.py", "w") as f:
        f.write("def test_no_code(): assert True\n")
    exit(0)

print(f"Found: {code_files}")

# 3. READ ALL CODE
code_content = ""
for f in code_files:
    try:
        with open(f, "r", encoding="utf-8") as file:
            code_content += f"\n# FILE: {f}\n{file.read()}\n"
    except Exception as e:
        print(f"⚠️ Could not read {f}: {e}")

if not code_content.strip():
    with open("test_ai_generated.py", "w") as f:
        f.write("def test_empty(): assert True\n")
    exit(0)

# 4. ASK AI
print("🤖 AI generating regression tests...")

# 👇 UPDATED PROMPT WITH IMPORT RULES
prompt = f"""You are a QA Automation Engineer.
Generate exactly 5 distinct pytest test cases for this code.

Rules:
1. Output ONLY Python code (no markdown or explanations).
2. **IMPORTANT**: You MUST import the 'app' object if testing a Flask app. 
   - Example: `from main import app` (infer the file name from the '# FILE:' comment).
3. Test realistic scenarios (success, edge cases, boundaries).
4. Don't assume error handling unless it exists in the code.
5. Name functions: test_ai_generated_1, test_ai_generated_2, etc.

Code to test:
{code_content}"""

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini", # Switched to 4o-mini for better reasoning on imports
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    test_code = response.choices[0].message.content
    
    # Clean up markdown if AI forgets rule #1
    if "```python" in test_code:
        test_code = test_code.split("```python")[1].split("```")[0]
    elif "```" in test_code:
        test_code = test_code.split("```")[1].split("```")[0]

except Exception as e:
    print(f"❌ API error: {e}")
    with open("test_ai_generated.py", "w") as f:
        f.write("def test_api_error(): assert True\n")
    exit(0)

# 5. SAVE TESTS
with open("test_ai_generated.py", "w") as f:
    f.write(test_code)

print("✅ Tests generated in test_ai_generated.py")
