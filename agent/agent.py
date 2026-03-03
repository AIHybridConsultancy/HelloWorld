import os
import json
import base64
from github import Github, InputGitTreeElement
import google.generativeai as genai

# --- Setup ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash-lite") # Current 2026 stable model

g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# Get Issue context
issue_number = int(os.environ["GITHUB_REF"].split("/")[-1]) if "issues" in os.environ.get("GITHUB_REF", "") else None
issue = repo.get_issue(number=issue_number) if issue_number else repo.get_issues(state="open")[0]

# --- Enhanced Prompt ---
prompt = f"""
You are an autonomous Senior Web Developer Agent. 
Task: Fully implement the requirements in the following issue.

Issue Title: {issue.title}
Issue Requirements:
{issue.body}

Instructions:
1. Identify all files needed (HTML, CSS, JS).
2. For each file, provide the relative path and the full content.
3. Respond ONLY with a valid JSON object in this format:
{{
  "files": [
    {{ "path": "index.html", "content": "..." }},
    {{ "path": "css/style.css", "content": "..." }}
  ],
  "summary": "Short explanation of what you built"
}}
Do not include markdown backticks or explanations outside the JSON.
"""

response = model.generate_content(prompt)
# Clean response text to ensure it's pure JSON
raw_json = response.text.replace("```json", "").replace("```", "").strip()
data = json.loads(raw_json)

# --- Multi-File Commit Logic ---
branch = "main"
master_ref = repo.get_git_ref(f"heads/{branch}")
master_sha = master_ref.object.sha
base_tree = repo.get_git_tree(master_sha)

elements = []
for f in data["files"]:
    element = InputGitTreeElement(path=f["path"], mode="100644", type="blob", content=f["content"])
    elements.append(element)

# Create the new tree and commit
tree = repo.create_git_tree(elements, base_tree)
parent = repo.get_git_commit(master_sha)
commit = repo.create_git_commit(f"🤖 AI Agent: {data['summary']} (Fixes #{issue.number})", tree, [parent])

# Update the branch pointer
master_ref.edit(commit.sha)

# Feedback
issue.create_comment(f"✅ **AI Implementation Complete!**\n\n**Changes:**\n{data['summary']}\n\nFiles updated: " + ", ".join([f['path'] for f in data['files']]))
