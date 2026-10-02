# Ask-your-data demo: build brief for Claude Code

Oct 2, 2026 · @Marton

## Goal

We are building an **ask-your-data assistant**. A business user asks a question about company data in plain English, for example "Which region sold the most units in 2025?", and an AI agent answers from the database. The agent reads the table schema, writes SQL, runs it through a read-only tool server and returns the answer together with its SQL, so anyone can check the number.

A good assistant does four things:

- It answers correctly from the data and never invents numbers.
- It recognises when a question is ambiguous, outside the data or not allowed, and asks back, explains or refuses instead of guessing.
- It learns the company's own definitions, such as "revenue means net revenue", and keeps them across conversations.
- It stays safe: access is read-only, and every answer can be traced to its SQL.

This repository builds the assistant three times, with LangGraph, Pydantic AI 2 and Strands Agents, plus an optional Amazon Bedrock AgentCore bonus. All data is synthetic.

## Context

The notebooks are teaching material for an internal lecture on agentic AI, mainly for data scientists. The presenter walks through each notebook cell by cell and has 10–15 minutes per framework. The aim is to show how the three frameworks differ on the same task, not to build a product.

Every notebook builds the assistant step by step, in the same three stages:

1. **A basic bot:** a helpful chatbot with the database tools and a minimal prompt, which shows how far a bare agent gets.
2. **Scenarios:** the bot recognises which situation it is in (answer, ask back, out of scope, not allowed), and the code takes a different path for each.
3. **Memory, examples and more:** the bot remembers what the user teaches it, follows verified examples, gets its SQL checked by a reviewer agent, and switches to a small local model.

**Simplicity is the main requirement.** The audience must understand every line, so each notebook shows the framework's own current API with as little code as possible.

### Rules that keep it teachable

- About 60 lines of framework code per notebook, in at most 18 short code cells of at most 15 lines each.
- Every code cell is followed by a speaker note of one or two sentences in Markdown.
- Each stage builds its own agent and needs only the setup cells, so the presenter can go through the notebooks framework by framework or stage by stage.
- Use the API that the framework's own docs show first today; no deprecated or legacy patterns (see "Current APIs" below).
- No wrapper layers that hide the framework. Shared helpers exist only for data, examples, the MCP server, prompts and output models.
- No extra error handling, logging, retries, classes or configuration systems unless the demo needs them.
- The same questions, prompts, examples and output models in all three notebooks, so only the framework differs.
- If a feature pushes a notebook past 15 minutes, move it to a clearly marked bonus cell or drop it.

## The build-up: three stages

The assistant answers business questions from a small sales database through an MCP tool server. Four test questions, one per scenario, show how the same questions are handled better at each stage.

| Scenario | Test question | Stage 1: basic bot | Stages 2 and 3 |
| --- | --- | --- | --- |
| `answer` | "Which region sold the most units in 2025?" | Answers, usually correctly. | Answers, with its SQL. |
| `clarify` | "What was our revenue in Q2 2026?" | Picks gross or net on its own, or reports both, without asking what we mean. | Asks "gross or net revenue?" and answers after the user's reply. |
| `out_of_scope` | "What was our profit margin in 2025?" | Up to the model: it may explain that costs are missing, or derive a "margin" from the revenue columns. | Says that the data has no costs and offers what it can answer. |
| `not_allowed` | "Delete all rows from 2024." | Up to the model: it may try a DELETE, which only the MCP server stops. | Refuses without calling a tool. |

The lesson of stage 1 is that a bare agent leaves these decisions to the model. Stage 2 makes them deliberate and testable, and stage 3 makes the bot learn.

| Stage | What we add | What happens | What the audience should notice |
| --- | --- | --- | --- |
| 1. A basic bot (about 3 minutes) | The two MCP tools, a minimal prompt ("You are a helpful chatbot…") and the `Answer` output. | The four test questions run without any rules. | How the framework connects to MCP tools and returns a typed answer, and that a bare prompt makes the bot guess. |
| 2. Scenarios (about 4 minutes) | The analyst prompt with one rule per scenario and the `Reply` output; plain Python takes a different path for each scenario. | The bot answers, asks back, declines and refuses as it should. The user's reply "net revenue" in the same conversation gets the answer, but a new conversation asks again. | How a typed output drives the flow, and how each framework keeps a conversation going: a thread id, the message history or a stateful agent. |
| 3. Memory, examples and more (about 7 minutes) | A glossary in the framework's own long-term memory, verified examples in the prompt, a reviewer agent that checks the SQL, and a one-line switch to `qwen3:8b` on Ollama. Bonus: a person approves each memory write. | The user's reply is saved to the glossary. A new conversation, even after a kernel restart, answers with net revenue without asking, and the reviewer approves the SQL or sends it back once. | Learning that outlives the conversation (an evolving agent), two agents cooperating, and what changes in accuracy and speed with a small local model. |

### Shared components, identical in all notebooks

- **Data:** one SQLite table, `sales` (month, region, product, units, gross_revenue, net_revenue), with 24 months × 3 regions × 3 products = 216 rows from a fixed seed. Net revenue is gross revenue minus discounts and returns, so the two answers differ visibly.
- **MCP server:** two read-only tools over stdio, `get_schema()` and `run_sql(query)`. `run_sql` accepts a single SELECT and returns at most 50 rows. The server is plain Python and knows nothing about the frameworks.
- **Output models:** `Answer(answer, sql)` for stage 1, `Reply(scenario, message, sql)` for stages 2 and 3, and `Review(approved, reason)` for the reviewer. They are Pydantic models passed to each framework as its output type, never pasted into prompts.
- **Prompts:** `prompts/basic.md` (stage 1), `prompts/analyst.md` (stages 2 and 3) and `prompts/reviewer.md` (stage 3), each with a `PROMPT_VERSION` header, read by one small loader.
- **Examples:** `data/examples.yaml`, five verified question → SQL pairs that stage 3 appends to the analyst prompt.
- **Glossary:** short "term → definition" entries. Each framework keeps them in its own native memory, always under `data/memory/<framework>/`, so stage 3 also works after a kernel restart.
- **Questions:** `data/questions.yaml` with the four test questions, the user's reply to the clarifying question, and the expected answers.

## Environment: one uv project, no lock file

All three frameworks fit in one environment at their latest releases; we tested this on 28 Sep 2026. It works because two optional extras are left out and the MCP SDK stays on version 2.1.

```bash
uv venv --python 3.13
uv pip install -e ".[dev]"
python -m ipykernel install --user --name agentic-demo   # one Jupyter kernel for all notebooks
```

Never run `uv lock` or `uv sync`, and never commit a `uv.lock`.

```toml
[project]
name = "agentic-demo"
version = "0.1.0"
description = "An ask-your-data assistant in LangGraph, Pydantic AI 2 and Strands (+ AgentCore), built in three stages for teaching"
requires-python = ">=3.13"
dependencies = [
    # LangChain / LangGraph 1.x; langchain[mcp] brings fastmcp 4 and mcp 2.x
    "langchain[mcp,openai,anthropic,ollama]>=1.4.2",
    "langgraph>=1.2.12",
    "langgraph-checkpoint-sqlite>=3.1.1",   # SqliteSaver + SqliteStore
    # Pydantic AI 2.x: its extras require openai>=3.19 and anthropic>=1.8
    "pydantic-ai-slim[openai,anthropic,mcp]>=2.51.0",
    # Strands WITHOUT [openai]/[anthropic]: those extras cap openai<3 and anthropic<1
    "strands-agents[ollama]>=1.57.1",
    # AgentCore SDK WITHOUT [strands-agents]: that extra caps mcp<2
    "bedrock-agentcore>=1.23.1",
    # Shared SDKs, stated explicitly because Strands uses them without declaring them
    "openai>=3.19.0",
    "anthropic>=1.8.0",
    "mcp>=2.1.1",       # resolves inside [2.1.1, 2.2) until Strands lifts its <2.2 cap
    "pyyaml>=6.0",      # data/questions.yaml, data/examples.yaml
]

[project.optional-dependencies]
dev = [
    "ruff>=0.16",
    "ty>=0.0.84",       # type checker that the /verify check runs (see AGENTS.md)
    "pre-commit>=4.6",
    "pytest>=9.1",
    "jupyterlab>=4.6",
    "ipykernel>=7.3",
    "python-dotenv>=1.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/agentic_demo"]
```

### Why the file looks like this

- `strands-agents` comes without its `[openai]` and `[anthropic]` extras. They cap `openai<3` and `anthropic<1`, while Pydantic AI 2.51 needs `openai>=3.19` and `anthropic>=1.8`. Strands' own OpenAI and Anthropic model classes ran correctly on the newer SDKs in our tests, but that is outside Strands' declared support, so re-test after every upgrade.
- `bedrock-agentcore` comes without `[strands-agents]`, which caps `mcp<2`; LangChain's MCP support needs `mcp>=2`.
- `mcp` resolves to 2.1.1, one release behind, because Strands caps it below 2.2.
- Every framework has a `>=` minimum pin. Without pins, uv silently fell back to ancient releases (strands-agents 0.0.1, pydantic-ai-slim 2.31.1); with them, a conflict fails loudly.
- `ty` is the type checker that the starter kit's `/verify` check runs. It has no dependencies and resolved cleanly in the same environment (dry run, 2 Oct 2026).
- Never add `langchain-mcp-adapters`, `bedrock-agentcore-starter-toolkit` or `strands-agents[litellm]`: each drags in an old cap (`mcp<2` or `openai<3`).
- Optional: before the talk, freeze the rehearsed versions with `uv pip compile pyproject.toml --extra dev -o requirements-frozen.txt`. That is a plain requirements file, not a `uv.lock`, and it protects against Pydantic AI's several releases a week.

### Tested versions

| Package | Version | Package | Version |
| --- | --- | --- | --- |
| langchain | 1.4.2 | strands-agents | 1.57.1 |
| langgraph | 1.2.12 | bedrock-agentcore | 1.23.1 |
| langgraph-checkpoint-sqlite | 3.1.1 | openai | 3.19.2 |
| pydantic-ai-slim | 2.51.0 | anthropic | 1.8.0 |
| mcp | 2.1.1 | ollama | 0.6.2 |
| fastmcp (via langchain) | 4.0.10 | Python | 3.13 |

### Keys and the local model

- `.env` holds the keys and is never printed; `.env.example` lists the same names without values: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OLLAMA_BASE_URL=http://localhost:11434/v1` (Pydantic AI requires it), `PYDANTIC_AI_NO_BANNER=1`, and optionally `LANGSMITH_TRACING` + `LANGSMITH_API_KEY`, `LOGFIRE_TOKEN`, `AWS_PROFILE` + `AWS_REGION=ap-southeast-1`.
- Local model: `ollama pull qwen3:8b` (5.2 GB, fine with 16 GB of RAM). Raise the context window, because Ollama defaults to 4k tokens on machines with less than 24 GB of VRAM.

All tests ran offline against fake model servers. The stage outlines below reuse the tested calls, but the follow-up turn in stage 2 and the reviewer wiring in stage 3 were not tested as a whole. Tool calling and answer quality with real models, especially `qwen3:8b`, still need a rehearsal with real keys.

## Current APIs, and the outdated ones to avoid

AI assistants and older tutorials still write outdated agent code. Everything in the left-hand columns below raises an error or a deprecation warning on the tested versions; use the right-hand column. Each row was checked on 28 Sep 2026 against the installed package or the official migration guide.

### Rules for every notebook

- Use top-level `await` in cells. Never call `asyncio.run(...)`, and never call Pydantic AI's `run_sync()` in a notebook: it raises `RuntimeError: This event loop is already running`. Strands' plain `agent(...)` call is fine.
- LangChain's MCP tools are async-only, so use `ainvoke`.
- Start local MCP servers from a `pathlib.Path` or from `sys.executable` plus arguments, never from a bare string path.
- Filter the `LangChainBetaWarning` for `langchain.mcp` and the cosmetic AgentCore import warnings before the talk.

### LangChain and LangGraph 1.x

| Don't use | Use instead |
| --- | --- |
| `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` |
| `prompt=`, `state_modifier=`, `pre_model_hook=` | `system_prompt=`, `middleware=[...]` (the old arguments raise `TypeError`) |
| `langchain_mcp_adapters`, `MultiServerMCPClient` (archived, needs `mcp<2`) | `from langchain.mcp import MCPAdapter`, then `async with MCPAdapter(Path("server.py")) as a: tools = await a.list_tools()` |
| `AgentExecutor`, `initialize_agent`, `LLMChain`, `langchain.memory`, `hub` | `create_agent` with a checkpointer and a store (legacy code lives in `langchain-classic`) |
| `MemorySaver()` | `InMemorySaver()`; `SqliteSaver` survives a restart |
| `config_schema=` with `config["configurable"]` | `context_schema=` plus `invoke(..., context=...)`, read in tools through `runtime.context` |
| `NodeInterrupt`, `interrupt_before=` for approvals | `interrupt()` plus `Command(resume=...)`, or `HumanInTheLoopMiddleware(interrupt_on={...})` |
| `response_format=("prompt", Schema)` | `response_format=Schema`, then `out["structured_response"]` |
| `langchain_community` `ChatOllama`, `langchain.chat_models.ChatOpenAI` | `"ollama:qwen3:8b"` / `"openai:..."` model strings, or `langchain_ollama.ChatOllama(model=..., num_ctx=...)` |
| `InjectedStore`, `get_store()` in tools | a `runtime: ToolRuntime` parameter, then `runtime.store` |
| `SqliteStore(sqlite3.connect(path))` | `SqliteStore.from_conn_string(path)` inside `with`, or a connection opened with `isolation_level=None` |
| `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY` | `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` |
| `draw_mermaid_png()` (calls a web service) | `draw_mermaid()` |

Also add `ModelCallLimitMiddleware(run_limit=15)`, because the default step limit is now about 10,000.

### Pydantic AI 2.x

| Don't use | Use instead |
| --- | --- |
| `result_type=` | `output_type=` |
| `result.data` | `result.output` |
| `mcp_servers=[...]`, `MCPServerStdio(...)` | `toolsets=[MCPToolset(Path("server.py"))]`, or `MCPToolset(StdioTransport(command=sys.executable, args=[...]))` |
| `async with agent.run_mcp_servers():` | `async with agent:` (one MCP process for every run in the block) |
| `OpenAIModel`; assuming `openai:` means Chat Completions | `"openai:..."` is now the Responses API; `"openai-chat:..."` or `OpenAIChatModel` is Chat Completions |
| `Agent("gpt-4o")` without a provider prefix | `Agent("openai:...")`, `Agent("anthropic:...")` |
| Ollama through `OpenAIModel(base_url=...)` | `"ollama:qwen3:8b"` with `OLLAMA_BASE_URL=http://localhost:11434/v1`, or `OllamaModel("qwen3:8b", provider=OllamaProvider(base_url=...))` |
| `DeferredToolCalls`, `DeferredToolset` | `output_type=[Reply, DeferredToolRequests]`, a tool with `requires_approval=True`, then resume with `DeferredToolResults(approvals={id: True})` |
| `history_processors=`, `prepare_tools=`, `builtin_tools=` | `capabilities=[...]` |
| `instrument=True` | `logfire.configure(); logfire.instrument_pydantic_ai()` |
| `output_retries=`, `result.usage()` | `retries={"output": 3}`, `result.usage` |
| `system_prompt=` for agents that receive another agent's history | `instructions=`, which is re-applied on every run |

Sync tools run on worker threads, so open the SQLite or JSON file inside the tool rather than sharing one connection.

### Strands Agents 1.x

| Don't use | Use instead |
| --- | --- |
| `agent.structured_output(Model, prompt)` | `agent(prompt, structured_output_model=Model)`, then `result.structured_output` |
| `with mcp_client: Agent(tools=mcp_client.list_tools_sync())` | `Agent(tools=[mcp_client])`, then `agent.cleanup()` at the end (`shutdown()` only flushes a memory manager; corrected on 2 Oct 2026) |
| `from mcp.server import FastMCP` (still on the Strands MCP page) | `from mcp.server.mcpserver import MCPServer` |
| `handoff_to_user` as an approval gate | `interventions=[HumanInTheLoop(allowed_tools=["*", "!add_memory"])]`; resume with an `interruptResponse` |
| `Agent(model="claude-...")` expecting Anthropic | a provider object; any string is a Bedrock model ID |
| `OllamaModel(model_id=...)` without a host, or a host ending in `/v1` | `OllamaModel("http://localhost:11434", model_id="qwen3:8b")` |
| `AnthropicModel(model_id=...)` without `max_tokens` | `AnthropicModel(model_id=..., max_tokens=2048)` |
| structured output with a small model and no cap | `limits={"turns": 10}`; failed validation otherwise retries without limit (open issue #4482) |
| `agent("...", user_id="x")` | `agent("...", invocation_state={"user_id": "x"})` |
| `strands.experimental.hooks` event names | `strands.hooks` (`BeforeToolCallEvent`, `AfterModelCallEvent`, ...) |
| `get_tracer(otlp_endpoint=...)` | `StrandsTelemetry().setup_otlp_exporter()` |
| default retries on HTTP 429 (up to minutes of waiting) | `retry_strategy=None` in the notebooks |
| `http_client=httpx.AsyncClient()` in `client_args` | nothing: openai 3.x and anthropic 1.x are built on `httpx2` |

### MCP Python SDK 2.x

| Don't use | Use instead |
| --- | --- |
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` (or the standalone `from fastmcp import FastMCP`) |
| a bare `@mcp.tool` on `MCPServer` | `@mcp.tool()` with parentheses |
| raising `ValueError` to tell the model what went wrong | `raise ToolError(...)` from `mcp.server.mcpserver.exceptions`; other exceptions reach the model only as a generic error |
| returning a plain `dict` | a `TypedDict` or Pydantic model, which becomes structured content |
| `streamablehttp_client` | `streamable_http_client` |
| `FastMCP("x", host=..., port=...)` | `server.run(transport="streamable-http", host=..., port=...)` |
| `mcp.get_context()` | a `ctx: Context` parameter on the tool |
| server-initiated sampling, roots, `ctx.elicit()` | leave them out of the demo; MCP 2.x removed or restricted them |

### Amazon Bedrock AgentCore (bonus only)

| Don't use | Use instead |
| --- | --- |
| `pip install bedrock-agentcore-starter-toolkit` | `npm install -g @aws/agentcore` (Node 20 or later); uninstall the Python toolkit first, because both install an `agentcore` command |
| `agentcore configure -e agent.py` | `agentcore create ...`, or `agentcore add agent --type byo` for existing code |
| `agentcore launch` / `agentcore launch --local` | `agentcore deploy` / `agentcore dev` |
| `agentcore invoke '{"prompt": "..."}'` | `agentcore invoke "..."` |
| `agentcore destroy` | `agentcore remove all && agentcore deploy` |
| memory strategies with `namespaces` | `namespaceTemplates` |
| hand-wired `MemoryClient` calls inside hooks | `AgentCoreMemorySessionManager(AgentCoreMemoryConfig(...))`, or `AgentCoreMemoryStore` inside Strands' `MemoryManager` |
| `bedrock-agentcore[strands-agents]` | plain `bedrock-agentcore`; the extra caps `mcp<2` |

## Repository structure

Shared code lives outside the notebooks, so each notebook shows only the framework-specific part. `AGENTS.md`, `CLAUDE.md` and `.claude/` come from our Claude Code starter kit and are in place before phase 1.

```text
agentic-demo/
├── AGENTS.md                  # starter kit: rules for any coding agent; phase 1 fills in the project sections
├── CLAUDE.md                  # starter kit: @AGENTS.md plus three Claude Code lines
├── .claude/                   # starter kit, used as is
│   ├── settings.json          # permissions, sandbox, UV_NO_SYNC=1, the two hooks
│   ├── hooks/
│   │   ├── guard_bash.py      # blocks git commit/push and commands that would print secrets
│   │   └── format_edited_file.py   # ruff fix + format on every edited Python file or notebook
│   ├── agents/
│   │   ├── verifier.md        # runs /verify on a small model and only reports
│   │   └── reviewer.md        # reviews the uncommitted diff before a commit
│   └── skills/verify/
│       └── SKILL.md           # /verify: lint, types, targeted tests, input probes, a few SI tests
├── README.md                  # setup in a few commands, how to run the demo
├── pyproject.toml             # as above; no uv.lock
├── .env.example               # key names only
├── .pre-commit-config.yaml    # ruff check + ruff format
├── .gitignore                 # .env, .venv/, uv.lock, data/*.db, data/memory/, CLAUDE.local.md, .claude/settings.local.json
├── docs/
│   └── brief.md               # this brief
├── data/
│   ├── seed.py                # builds data/sales.db from a fixed seed, writes the expected answers
│   ├── questions.yaml         # one test question per scenario, plus the reply to the clarifying question
│   └── examples.yaml          # five verified question → SQL pairs (stage 3)
├── mcp_server/
│   └── server.py              # MCPServer with get_schema() and run_sql()
├── prompts/
│   ├── basic.md               # stage 1: a minimal prompt
│   ├── analyst.md             # stages 2–3: one rule per scenario
│   └── reviewer.md            # stage 3
├── src/agentic_demo/
│   ├── __init__.py
│   ├── models.py              # Answer, Reply, Review
│   ├── prompts.py             # load_prompt(name) -> str, load_examples() -> str
│   └── paths.py               # repo-relative paths: DB, server script, questions, examples, memory folder
├── notebooks/
│   ├── 00_setup_check.ipynb   # keys, Ollama, MCP server, versions
│   ├── 01_langgraph.ipynb     # stages 1–3
│   ├── 02_pydantic_ai.ipynb   # stages 1–3
│   └── 03_strands_agentcore.ipynb   # stages 1–3, plus the AgentCore bonus
├── bonus/agentcore/           # optional AgentCore project, deployed the day before
└── tests/
    ├── test_mcp_server.py     # SELECT only, 50-row cap, schema
    ├── test_shared.py         # prompts load, models validate, seed is reproducible, examples run
    └── integration/
        └── test_mcp_stdio.py  # SI test: starts the server over stdio and calls both tools
```

### Shared components in detail

- **`data/seed.py`** builds 216 rows with a fixed seed (42): 24 months from Oct 2024 to Sep 2026, stored as `'YYYY-MM'` text, three regions (APAC, EMEA, Americas) and three products (Basic, Pro, Enterprise). `gross_revenue` is units × list price, and `net_revenue` is gross revenue minus a 5–15% discount and 1–4% returns, so net is visibly lower. The script also writes the expected answers into `questions.yaml`.
- **`data/questions.yaml`** holds the four test questions:

```yaml
# seed.py fills in the expected values
- scenario: answer
  question: Which region sold the most units in 2025?
  expected: null
- scenario: clarify
  question: What was our revenue in Q2 2026?
  reply: Net revenue. Please remember that revenue always means net revenue for us.
  expected_gross: null
  expected_net: null
- scenario: out_of_scope
  question: What was our profit margin in 2025?
- scenario: not_allowed
  question: Delete all rows from 2024.
```

- **`data/examples.yaml`** holds five verified question → SQL pairs that show our conventions: quarters as month ranges (`'2026-04'` to `'2026-06'`), "the last N months" counted back from the latest month in the table, money rounded to whole numbers, and gross or net always named. No example uses the bare word "revenue", so the examples never settle the gross-or-net question; that stays the glossary's job. `load_examples()` formats them as a short Markdown block.
- **`src/agentic_demo/models.py`** defines the three output models. All fields are required, the safest shape for every provider's structured-output mode, and the field descriptions guide the model, so the prompts never repeat the schema.

```python
from typing import Literal

from pydantic import BaseModel, Field


class Answer(BaseModel):  # stage 1
    answer: str = Field(description="The answer in one or two sentences, with the number.")
    sql: str = Field(description="The SELECT statement that produced the answer.")


class Reply(BaseModel):  # stages 2 and 3
    scenario: Literal["answer", "clarify", "out_of_scope", "not_allowed"]
    message: str = Field(description="The answer with its number, the clarifying question, or why we cannot help.")
    sql: str = Field(description="The SELECT that produced the answer; empty if no query was run.")


class Review(BaseModel):  # stage 3
    approved: bool
    reason: str = Field(description="Why the SQL is right, or what to fix.")
```

- **`mcp_server/server.py`** follows the shape we tested with all three frameworks:

```python
from typing import TypedDict
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError   # only ToolError text reaches the model

server = MCPServer("sales-db", instructions="Read-only access to the demo `sales` table.")

class SqlResult(TypedDict):   # a TypedDict return becomes structured content; a bare dict does not
    columns: list[str]
    rows: list[list]
    truncated: bool

@server.tool()                # parentheses are required
def get_schema() -> str:
    """Return the CREATE TABLE statement of the `sales` table."""

@server.tool()
def run_sql(query: str) -> SqlResult:
    """Run ONE read-only SELECT statement and return at most 50 rows."""
    # reject anything but a single SELECT, open the DB with ?mode=ro, fetchmany(51), raise ToolError on problems

if __name__ == "__main__":
    server.run(transport="stdio")
```

- **The prompts** each start with a `PROMPT_VERSION: 1` line; `load_prompt(name)` strips it and returns the text.
  - `basic.md` is deliberately minimal, for example: "You are a helpful chatbot. Answer questions about our sales data, and use the tools to look at the data."
  - `analyst.md` gives one rule per scenario. Answer from `run_sql` when the table can answer. When a term or period could mean two things in the data, such as revenue, which can be gross or net, ask one short question with the options and run no query. When the data cannot answer, say what it does cover. Refuse anything other than reading data, without calling a tool. It also says to follow the company's definitions in the glossary, when there are any, instead of asking, and to take numbers only from `run_sql`.
  - `reviewer.md` says to compare the SQL with the question and the glossary, and to approve only if the definitions match.
- **The glossary** lives in each framework's native memory under `data/memory/<framework>/`: a `SqliteStore` for LangGraph, a JSON file behind a typed dependency for Pydantic AI, and a `FileMemoryStore` for Strands. A reset cell at the start of stage 3 deletes only that notebook's folder, so every rehearsal starts clean.

## Notebook outlines

Every notebook follows the same frame, so the audience can compare them side by side. The API calls below were checked in the tested environment; the exact prompts and wording are up to Claude Code.

### Common frame

1. **Title** (Markdown): the framework in one sentence, the three stages and the time budget.
2. **Setup** (code): `load_dotenv()`, imports, the shared models, prompts and questions, the MCP tools, and one visible line that chooses the model.
3. **Stages 1–3**: a Markdown heading each, two to five short code cells, and a speaker note after every code cell. Each stage builds its own agent from the setup cells only. From stage 2 on, a short `match` on `reply.scenario` prints the answer and its SQL, the question back, or the refusal.
4. **Wrap-up** (Markdown): three bullets on what was easy and what was hard in this framework.

### 01_langgraph.ipynb: an explicit graph with built-in memory

1. Setup: filter `LangChainBetaWarning` before importing `langchain.mcp`; `MODEL = "anthropic:claude-sonnet-4-6"` or an `"openai:..."` model; `async with MCPAdapter(Path(SERVER)) as mcp: tools = await mcp.list_tools()`, then print the tool names. Our test found that the tools keep working after the block; if they don't, keep the runs inside it.
2. Stage 1: `bot = create_agent(MODEL, tools, system_prompt=load_prompt("basic"), response_format=Answer, middleware=[ModelCallLimitMiddleware(run_limit=15)])`; for each test question, `out = await bot.ainvoke({"messages": [("user", q)]})`, then show `out["structured_response"]`.
3. Stage 2: the same call with `load_prompt("analyst")`, `response_format=Reply` and `checkpointer=InMemorySaver()`. Each question runs in its own thread (`{"configurable": {"thread_id": ...}}`). The reply to the clarifying question goes into the same thread and gets the answer; in a new thread, the bot asks back again.
4. Stage 3, memory and examples: a `SqliteStore` under `data/memory/langgraph/` and two tools that take `runtime: ToolRuntime`: `remember(term, definition)` writes with `runtime.store.put(("glossary",), ...)`, and `glossary()` reads with `runtime.store.search(("glossary",))`. The analyst gets these tools, `system_prompt=load_prompt("analyst") + load_examples()` and `store=store`. Run the clarifying question and the reply in one thread, then the question again in a new thread.
5. Stage 3, reviewer: a `StateGraph` with an `analyst` node and a `reviewer` node (a second `create_agent` with the `glossary` tool and `response_format=Review`). A conditional edge after the analyst skips the review unless the scenario is `answer`, and one after the reviewer sends a rejected answer back once. Print `graph.get_graph().draw_mermaid()` and run with a new `thread_id`.
6. Stage 3, model swap: `MODEL = "ollama:qwen3:8b"`, or `ChatOllama(model="qwen3:8b", num_ctx=16384)` for a larger context; rebuild, re-run the new-thread question and time it.
7. Bonus: `HumanInTheLoopMiddleware(interrupt_on={"remember": {"allowed_decisions": ["approve", "reject"]}})`, invoke with `version="v2"`, show `out.interrupts`, resume with `Command(resume={"decisions": [{"type": "approve"}]})`.
8. Talking points: explicit, visual control flow and memory that persists out of the box, at the cost of more concepts to explain (state, threads, middleware).

### 02_pydantic_ai.ipynb: typed Python with the least magic

1. Setup: check that `OLLAMA_BASE_URL` is set; `MODEL = "anthropic:claude-sonnet-4-6"`, and note that `"openai:..."` now means the Responses API; `sales = MCPToolset(Path(SERVER))`.
2. Stage 1: `bot = Agent(MODEL, output_type=Answer, toolsets=[sales], instructions=load_prompt("basic"))`; inside `async with bot:`, run `r = await bot.run(q)` for each test question and show `r.output`.
3. Stage 2: `analyst = Agent(MODEL, output_type=Reply, toolsets=[sales], instructions=load_prompt("analyst"))`. Runs are independent, so the reply to the clarifying question continues the conversation with `await analyst.run(reply, message_history=r.all_messages())`, while a new run without the history asks back again. Talking point: Pydantic AI could also take one output model per scenario, as a list in `output_type`; the demo keeps `Reply` so all notebooks match.
4. Stage 3, memory and examples: `@dataclass class Deps: glossary_path: Path; glossary: dict[str, str]`, loaded from `data/memory/pydantic_ai/glossary.json`. The analyst becomes `Agent(MODEL, deps_type=Deps, output_type=Reply, toolsets=[sales], instructions=load_prompt("analyst") + load_examples())`. A function registered with `@analyst.instructions` appends the current glossary from `ctx.deps`, and `@analyst.tool def remember(ctx, term, definition)` updates the dict and writes the JSON file. Run the clarifying question and the reply with `message_history`, then the question again in a fresh run with freshly loaded `Deps`.
5. Stage 3, reviewer: `reviewer = Agent(MODEL, deps_type=Deps, output_type=Review, instructions=load_prompt("reviewer"))` gets the same glossary function through `reviewer.instructions(...)`. A plain Python loop runs the analyst, then the reviewer when the scenario is `answer`, and re-runs the analyst once with the reviewer's reason if it rejects.
6. Stage 3, model swap: pass `model="ollama:qwen3:8b"` to `run(...)`, a one-argument swap for a single run.
7. Optional, one cell: `with analyst.override(model=TestModel()):` runs the agent offline, which shows why teams like it for testing.
8. Bonus: `requires_approval=True` on `remember`, `output_type=[Reply, DeferredToolRequests]`, then approve with `DeferredToolResults(approvals={call.tool_call_id: True})`.
9. Talking points: plain typed Python and easy offline tests, but memory, persistence and the review loop are yours to write.

### 03_strands_agentcore.ipynb: the least code and a managed path to production

1. Setup: `model = AnthropicModel(model_id="claude-sonnet-4-6", max_tokens=2048)` or `OpenAIModel(model_id=...)`; never a bare string, which Strands treats as a Bedrock model ID. `sales = MCPClient(lambda: stdio_client(StdioServerParameters(command=sys.executable, args=[SERVER])))` is shared by all agents in the notebook.
2. Stage 1: a Strands agent keeps its conversation, so each test question gets a fresh `Agent(model=model, tools=[sales], system_prompt=load_prompt("basic"), callback_handler=None, retry_strategy=None)` (or an emptied `agent.messages`), called with `agent(q, structured_output_model=Answer, limits={"turns": 10})`; show `result.structured_output`.
3. Stage 2: the same with `load_prompt("analyst")` and `structured_output_model=Reply`. The reply to the clarifying question is simply the next call on the same agent; a fresh agent asks back again.
4. Stage 3, memory and examples: `FileMemoryStore(name="glossary", description="Business definitions", writable=True, storage=LocalFileStorage(MEMORY_DIR))` inside `MemoryManager(stores=[store], add_tool_config=True)`, which gives the agent `search_memory` and `add_memory` tools and injects relevant entries automatically. The analyst's prompt is `load_prompt("analyst") + load_examples()`.
5. Stage 3, reviewer: `reviewer = Agent(model=model, name="reviewer", system_prompt=load_prompt("reviewer"), memory_manager=memory, callback_handler=None)`. The analyst gets it as a tool: `Agent(model=model, tools=[sales, reviewer.as_tool(description="Checks your SQL against the question and the glossary; call it before answering")], memory_manager=memory, system_prompt=..., callback_handler=None, retry_strategy=None)`. Run the clarifying question and the reply on one agent, then the question on a fresh agent with the same memory; the model itself decides when to use the memory and the reviewer.
6. Stage 3, model swap: `model = OllamaModel("http://localhost:11434", model_id="qwen3:8b")`, rebuild and re-run.
7. Bonus: `interventions=[HumanInTheLoop(allowed_tools=["*", "!add_memory"])]`, check `r.stop_reason == "interrupt"`, and resume with an `interruptResponse`.
8. Bonus, prepared the day before: invoke the same agent deployed on AgentCore Runtime (`agentcore invoke "..."`), and show a definition that AgentCore Memory extracted on its own. Extraction takes 20–40 seconds or more, so pre-populate it.
9. Finish with `cleanup()` on the agents: the shared MCP process stops when the last agent that uses it is cleaned up.
10. Talking points: the least code and a managed road to production, but the model decides the flow, and the AWS extras need setup.

## Instructions for Claude Code

You get this brief as `docs/brief.md`, together with `AGENTS.md`, `CLAUDE.md` and `.claude/` from our starter kit. Those files carry the general rules: uv without a lock file, minimal modifications, read-only git, how to handle secrets, and the `/verify` check after a code change. Use them as they are; the only change is the project sections of `AGENTS.md` in phase 1. Claude Code never commits; commits are made by hand after the checks.

### Build order

Build the repo in six phases and stop after each one for review.

1. **Scaffold:** the project sections of `AGENTS.md` (text below), `pyproject.toml` exactly as above, `.env.example`, `.gitignore`, pre-commit with ruff, `README.md`, and `00_setup_check.ipynb`, which prints package versions, checks that keys exist without printing them, pings Ollama, and starts the MCP server to list its tools.
2. **Shared parts:** `data/seed.py`, `questions.yaml`, `examples.yaml`, the MCP server, the output models, the prompts and their loaders, with unit tests and the SI test.
3. **`01_langgraph.ipynb`**, stage by stage: get stage 1 running before writing stage 2.
4. **`02_pydantic_ai.ipynb`**, the same way.
5. **`03_strands_agentcore.ipynb`**, without the AgentCore bonus.
6. **Bonus:** the AgentCore project in `bonus/agentcore/` and the bonus cells.

### Acceptance criteria

*Environment*

- [ ] `uv venv --python 3.13 && uv pip install -e ".[dev]"` works from a clean clone, no `uv.lock` exists, and `uv pip check` is clean.
- [ ] `pytest` passes offline, and ruff and ty are clean on `src/`, `mcp_server/`, `data/` and `tests/`.
- [ ] `AGENTS.md` has its project sections filled in, and `CLAUDE.md` and `.claude/` are unchanged.

*Shared parts*

- [ ] `seed.py` is reproducible, writes 216 rows with `'YYYY-MM'` months, and net revenue is always below gross revenue.
- [ ] `run_sql` rejects anything but a single SELECT and returns at most 50 rows; unit tests prove both, and the SI test starts the server over stdio and calls both tools.
- [ ] Every SQL in `examples.yaml` runs on the seeded database, and no example uses the bare word "revenue".
- [ ] Prompts load with their version, and `Answer`, `Reply` and `Review` are passed as output types, never described in prompts.

*Notebooks*

- [ ] Each notebook runs stages 1–3 top to bottom with a cloud model and with `qwen3:8b`, and each stage needs only the setup cells.
- [ ] With the cloud model, stage 2 returns the expected scenario for all four test questions, and the clarifying conversation ends with the revenue figure the user asked for.
- [ ] In stage 3, a new conversation answers the revenue question with net revenue without asking, also after a kernel restart, and the reviewer checks that answer.
- [ ] The model changes in one visible line or argument.
- [ ] Each notebook has about 60 lines of framework code, at most 18 code cells of at most 15 lines, and a speaker note after every code cell.
- [ ] Executed outputs are saved as a fallback for the live demo.
- [ ] None of the outdated forms listed under "Current APIs" appears anywhere in the repo.

*Nice to have*

- [ ] Bonus approval cells in all three notebooks.
- [ ] AgentCore bonus: a runtime deployed to ap-southeast-1 and a pre-populated memory.
- [ ] A small scoreboard: 4 test questions × 3 frameworks × 2 models, showing whether the scenario and the number were right, the seconds and the tokens.
- [ ] `OFFLINE=1` switches every notebook to fake models (a LangChain fake chat model, Pydantic AI `TestModel`, a tiny Strands `Model` subclass) for rehearsals and CI.
- [ ] Learning from use: an answer that the reviewer approved is saved as a new example under `data/memory/`, and the next run picks it up.

### AGENTS.md: project sections

In phase 1, replace the comment under "Project", the bullet under "Layout" and the comment under "Project notes" in `AGENTS.md` with the text below. Leave the rest of `AGENTS.md`, `CLAUDE.md` and all of `.claude/` unchanged. These rules then stay loaded in every session.

```markdown
## Project

Teaching demo for an internal lecture on agentic AI: an ask-your-data assistant that answers business
questions from a small synthetic SQLite sales table through a read-only MCP server. It is built in
LangGraph, Pydantic AI 2 and Strands Agents (plus an optional AgentCore bonus), each notebook in the same
three stages: a basic bot, scenarios, then memory, examples and a reviewer. The notebooks are the
deliverable, and each must be explainable in 10–15 minutes, so simplicity beats completeness.
Full spec: `docs/brief.md`.

## Layout

- `notebooks/` the deliverables; `src/agentic_demo/` shared models, loaders and paths; `mcp_server/` the
  read-only MCP server; `prompts/` versioned prompts; `data/` seed script, questions and examples (the
  generated `*.db` and `memory/` are gitignored); `tests/` pytest, `tests/integration/` SI tests;
  `bonus/agentcore/`; `docs/brief.md`.

## Project notes

- Use only the current APIs in `docs/brief.md`; when unsure, check the installed package, not memory.
- Never add `strands-agents[openai|anthropic|litellm]`, `bedrock-agentcore[strands-agents]`,
  `langchain-mcp-adapters` or `bedrock-agentcore-starter-toolkit`: they break the shared environment.
- Notebooks use top-level `await`; never `asyncio.run(...)` or Pydantic AI's `run_sync()` in a cell.
- Prompts live in `prompts/*.md` with a `PROMPT_VERSION` header and load through `load_prompt`;
  output schemas are Pydantic models passed to the framework, never pasted into prompts.
- Before handing back a notebook, run it top to bottom (`jupyter execute`) and save the outputs.
- The local model is `qwen3:8b` on Ollama at `localhost:11434`.
- Notebook runs need network access (model APIs, Ollama) and write Jupyter files in the home folder;
  if the sandbox blocks this, stop and ask, and never change the sandbox settings.
- Memory lives under `data/memory/<framework>/`; each notebook's reset cell deletes only its own folder.
```

### Kickoff prompt

```text
Read docs/brief.md. We are building teaching notebooks for an ask-your-data assistant, so keep every
file as simple as the brief demands. Work in the six phases of "Build order" and stop after each phase
for my review. Start with phase 1: fill in the project sections of AGENTS.md, create the scaffold with
pyproject.toml exactly as in the brief, install it with uv (no lock file) and build
00_setup_check.ipynb. Then show me the versions it prints.
```

## Sources

All pages were opened, and all packages installed and tested, on 28 Sep 2026; the Strands cleanup behaviour and the `ty` version were checked on 2 Oct 2026.

- **Comparison (for people; Claude Code does not need it):** [Agentic orchestrators: LangGraph vs Pydantic AI 2 vs Strands + AgentCore](https://claude.ai/code/artifact/b64b9a94-122b-4b9f-afe4-29fc54fa3c59)
- **LangChain and LangGraph:** [LangChain v1 migration](https://docs.langchain.com/oss/python/migrate/langchain-v1) · [LangGraph v1 migration](https://docs.langchain.com/oss/python/migrate/langgraph-v1) · [MCP in LangChain](https://docs.langchain.com/oss/python/langchain/mcp) · [moving off langchain-mcp-adapters](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters) · [tracing with LangSmith](https://docs.langchain.com/langsmith/trace-with-langgraph)
- **Pydantic AI:** [changelog](https://pydantic.dev/docs/ai/project/changelog/) · [MCP client](https://pydantic.dev/docs/ai/mcp/client/) · [deferred tools](https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/) · [Ollama](https://pydantic.dev/docs/ai/models/ollama/) · [Logfire](https://pydantic.dev/docs/ai/integrations/logfire/) · [run_sync in Jupyter, issue #3014](https://github.com/pydantic/pydantic-ai/issues/3014)
- **Strands:** [MCP tools](https://strandsagents.com/docs/user-guide/sdk/tools/mcp-tools/) · [structured output](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/) · [human in the loop](https://strandsagents.com/docs/user-guide/concepts/agents/interventions/human-in-the-loop/) · [Ollama](https://strandsagents.com/docs/user-guide/sdk/model-providers/ollama/) · [agents as tools](https://strandsagents.com/docs/user-guide/concepts/multi-agent/agents-as-tools/) · [structured-output retries, issue #4482](https://github.com/strands-agents/harness-sdk/issues/4482)
- **AgentCore:** [CLI getting started](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-cli.html) · [Strands with AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html) · [starter-toolkit migration](https://github.com/awslabs/agentcore-samples/blob/main/MIGRATION.md)
- **MCP:** [Python SDK v2 migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/) · [fastmcp 4.0.0 release](https://github.com/PrefectHQ/fastmcp/releases/tag/v4.0.0) · [mcp release history](https://pypi.org/project/mcp/#history)
- **Dependency metadata:** [langchain](https://pypi.org/project/langchain/) · [pydantic-ai-slim](https://pypi.org/project/pydantic-ai-slim/) · [strands-agents](https://pypi.org/project/strands-agents/) · [bedrock-agentcore](https://pypi.org/project/bedrock-agentcore/) · [ty](https://pypi.org/project/ty/)