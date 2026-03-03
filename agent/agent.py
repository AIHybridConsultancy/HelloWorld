import os
import google.generativeai as genai
from github import Github

# Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Setup GitHub
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# Get latest issue
issues = repo.get_issues(state="open")
issue = issues[0]

prompt = f"""
You are a senior software developer.

Analyze this GitHub issue and propose:
1. Root cause
2. Implementation plan
3. Example code if relevant

Issue Title: {issue.title}

Issue Body:
{issue.body}
"""

response = model.generate_content(prompt)

issue.create_comment(response.text)