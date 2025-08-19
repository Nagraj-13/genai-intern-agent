# LawVriksh GenAI Engineer

# Assignments

Deadline: Submit within 2 days after receiving the assignment
**Note:** A basic frontend for the blog platform will be provided; focus solely on
backend/API and reporting.

## Assignment 1: Develop Agentic Blog Support System

**Scenario:**
You have access to a supplied React-based blog frontend. Build and expose
backend APIs that enable an agentic workflow for blog post analysis and keyword
recommendation.
**Core Requirements:**
 **API Development**
Initialize a fresh backend project Node.js/Express or Python/FastAPI, no
boilerplate provided.
Endpoints to create:
POST /api/analyze-blogs
Input: array of existing blog texts.
Output: for each post, sentiment metrics, extracted key topics, and
initial keyword suggestions.
POST /api/recommend-keywords
Input: current draft blog text (partial or full), cursor context
(optional), and user profile JSON.
Output: a dynamic ranked list of suggested words or phrases to
insert next, as well as a real-time readability/relevance score and
estimated token usage.
Secure both endpoints via API key or Bearer JWT.


 **Agentic Workflow During Blog Writing**
Implement an agent (server-side orchestrator) that operates in real-time
during the blog writing process:
 Periodically analyzes the evolving draft using /api/recommend-keywords.
 Refines suggestions by referencing patterns learned from /api/analyze-
blogs run on past blog data.
The agent should suggest new keywords inline or highlight weak sections
(based on scoring) as the user types.
Handle intermittent failures with retries (up to 3 with exponential backoff).
 **AI Model Integration**
Integrate an LLM (e.g., OpenAI GPT‑4, Llama) of your choice—justify
selection in your report.
Craft prompt templates optimizing token efficiency (include before/after
token counts).
Return token usage per API response.
 **Blog Scoring System**
Define and implement a scoring algorithm combining:
Keyword relevance (semantic similarity and frequency).
Readability metric (e.g., Flesch‑Kincaid).
User profile factors (preferred topics, reading level).
Score range should be 0100.
**Deliverables:**
GitHub repo genai-intern-agent with source under src/.
Postman collection demonstrating both endpoints with sample inputs/outputs.
REPORT.md covering architecture, model/prompt rationale, scoring formula, and
token efficiency.
Plagiarism on report is 30% accepted , otherwise your submission will be
discarded


Note: Assigment 2 is optional , if you completed assignment 2 then this will be
considered as a bonus and your chances of selection will be higher

## Assignment 2: Propose Agentic Control Feature (optional: do it for

## bonus but focus on first assignment first then think about this

## one)

**Scenario:**
After reviewing the LawVriksh site (both provided frontend and your backend
work), propose a new agentic control feature that could automate a key process,
improving user experience or content quality.
**Core Requirements:**
 **Feature Identification**
Select one area (e.g., comment moderation, content tagging, personalized
notifications).
Describe the current manual or semi-automated process.
 **Agent Design Proposal**
Outline how an agent would operate: inputs, decision logic, outputs, and
integrations.
Specify which APIs, models, or data sources it would leverage.
 **Impact Analysis**
Explain expected benefits (e.g., time savings, higher content relevance).
Identify potential risks or failure modes and mitigation strategies.
 **Deliverables:**
Extend your REPORT.md with a dedicated section for this proposal
Include any diagrams or pseudo-code snippets in Markdown.
Plagiarism on report is 30% accepted , otherwise your submission will be
discarded
**Evaluation Criteria:**


 Clarity and feasibility of the proposed agentic feature.
 Depth of integration details and technical reasoning.
 Quality of impact and risk analysis.
 Overall report structure, readability, and originality.


