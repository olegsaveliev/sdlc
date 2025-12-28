import os
import glob
import openai
import re

# 1. SETUP
client = openai.OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# 2. FIND CODE
all_files = glob.glob("*.py")
code_files = [f for f in all_files if not f.startswith("test_") and "generate_unit_tests" not in f]

if not code_files:
    print("❌ No source code found.")
    exit(0)

# 3. READ CODE
full_code = ""
for f in code_files:
    with open(f, "r") as file: full_code += f"\n# FILE: {f}\n{file.read()}\n"

# 4. ASK AI
print("🧠 AI is writing tests...")
prompt = f"""
You are a Python Code Generator.
Task: Write a executable pytest file for the code below.

Code:
{full_code}

STRICT RULES:
1. Return ONLY valid Python code.
2. DO NOT write explanations, intro text, or markdown.
3. If the code is just a print statement, write a test that checks if the file runs without error.
"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

raw_content = response.choices[0].message.content

# 5. THE CLEANER (FIXED)
# We look for "import" or "from", and capture EVERYTHING (.*) until the end of the string
match = re.search(r'((?:import|from)\s+.*)', raw_content, re.DOTALL)

if match:
    clean_code = match.group(1)
else:
    # Fallback: Just strip markdown if no imports found
    clean_code = raw_content.replace("```python", "").replace("```", "")

# 6. SAVE
with open("test_auto_generated.py", "w") as f:
    f.write(clean_code)

print("✅ Generated cleaned tests.")
