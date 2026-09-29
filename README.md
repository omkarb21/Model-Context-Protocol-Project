# MCP Chat

**A terminal chat app that shows how an LLM, an MCP client, and an MCP server work together.**

MCP Chat lets you talk to Claude from the command line and work with a set of documents that live behind an MCP server. Claude can read and edit those documents by calling **tools**. You can pull documents into the conversation with `@mentions`, which are backed by **resources**. You can run ready-made workflows with `/commands`, which are backed by **prompts**. Those are the three core primitives of the [Model Context Protocol](https://modelcontextprotocol.io).

The codebase is small on purpose, so you can read all of it in one sitting and see where each MCP concept lives.

```
> Tell me about @report.pdf
Response:
The report details the state of a 20m condenser tower.

> /format plan.md
Response:
# Project Plan
...
```

---

## Features

- **Agentic tool use.** Claude decides when to call MCP tools such as `read_doc_contents` and `edit_document`. The app runs each call and feeds the result back, looping until Claude has a final answer.
- **`@` document mentions.** Type `@` to get a list of documents that the server exposes as MCP resources. A mentioned document's contents go straight into the prompt, so no tool call is needed.
- **`/` slash commands.** The server's MCP prompts show up as slash commands with tab completion and argument hints.
- **Multiple servers.** You can pass extra MCP server scripts on the command line. The app collects their tools and sends each call to the server that owns the tool.
- **Rich terminal UI.** Built on `prompt_toolkit`, with autocompletion, inline suggestions, and input history.

---

## How it works

```
┌──────────────────────┐    Messages API     ┌──────────────────┐
│      CLI (you)       │ ◀─────────────────▶ │  Claude (LLM)    │
│  prompt_toolkit UI   │   tools + messages  │  Anthropic API   │
└─────────┬────────────┘                     └──────────────────┘
          │  Chat loop (core/chat.py)
          │  tool_use → execute → tool_result → repeat
          ▼
┌──────────────────────┐   stdio (JSON-RPC)  ┌──────────────────┐
│     MCP Client       │ ◀─────────────────▶ │   MCP Server     │
│   mcp_client.py      │                     │  mcp_server.py   │
│  ClientSession       │                     │  FastMCP         │
└──────────────────────┘                     │  • tools         │
                                             │  • resources     │
                                             │  • prompts       │
                                             └──────────────────┘
```

1. `main.py` starts the MCP server as a **subprocess** and connects to it over **stdio** through `MCPClient`.
2. On startup, the CLI fetches the **resource** `docs://documents` to get the document IDs for `@` completion, and the list of **prompts** for `/` completion.
3. When you send a message:
   - **`/command <doc_id>`** gets the matching MCP prompt from the server and adds its messages to the conversation.
   - **`@doc_id` mentions** are resolved by reading `docs://documents/{doc_id}`, and the contents are added to the prompt as context.
4. The conversation goes to Claude together with every tool collected from the connected MCP servers.
5. If Claude replies with `stop_reason == "tool_use"`, `ToolManager` finds the server that owns the tool, calls it, and returns the result to Claude. This repeats until Claude gives a final text answer.

### MCP primitives in this project

| Primitive    | Name / URI                  | Purpose                                                        |
|--------------|-----------------------------|----------------------------------------------------------------|
| **Tool**     | `read_doc_contents`         | Return the contents of a document by ID                        |
| **Tool**     | `edit_document`             | Replace an exact string in a document with new text            |
| **Resource** | `docs://documents`          | List all document IDs (JSON)                                   |
| **Resource** | `docs://documents/{doc_id}` | Return one document's contents (templated resource, plain text) |
| **Prompt**   | `format`                    | Tell Claude to rewrite a document in Markdown with `edit_document` |

---

## Tech stack

| Technology | Role |
|------------|------|
| [Python 3.10+](https://www.python.org/) | Language; the app is fully `asyncio`-based |
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | Calls Claude through the Messages API with tool use |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp[cli]`) | `FastMCP` for the server, `ClientSession` + `stdio_client` for the client |
| [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) | Interactive CLI with completion, auto-suggest, key bindings, and history |
| [Pydantic](https://docs.pydantic.dev/) | Parameter descriptions (`Field`) for tool and prompt arguments, which become the JSON schema Claude sees |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads configuration from `.env` |
| [uv](https://github.com/astral-sh/uv) | Fast package and project manager (optional; `uv.lock` included) |

---

## Project structure

```
.
├── main.py            # Entry point: loads config, starts MCP clients/servers, launches the CLI
├── mcp_server.py      # MCP server (FastMCP): document store + tools, resources, prompts
├── mcp_client.py      # MCP client wrapper around ClientSession over stdio
├── core/
│   ├── claude.py      # Thin wrapper around the Anthropic Messages API
│   ├── chat.py        # Agentic loop: send → handle tool_use → return tool_result → repeat
│   ├── cli_chat.py    # Adds @mention resource injection and /command prompt handling
│   ├── cli.py         # prompt_toolkit UI: completer, auto-suggest, key bindings
│   └── tools.py       # ToolManager: collects tools from all clients and routes calls
├── pyproject.toml
└── uv.lock
```

---

## Installation

### Prerequisites

- **Python 3.10 or newer**
- An **Anthropic API key** from the [Anthropic Console](https://console.anthropic.com/)
- *(Optional, recommended)* **[uv](https://github.com/astral-sh/uv)**

### 1. Clone the repository

```bash
git clone <your-repo-url> mcp-chat
cd mcp-chat
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
# Claude model to use, e.g. claude-sonnet-5
CLAUDE_MODEL="claude-sonnet-5"

# Your Anthropic API key
ANTHROPIC_API_KEY="sk-ant-..."

# 1 = launch the MCP server with `uv run`, 0 = launch it with `python`
USE_UV=1
```

> `.env` is listed in `.gitignore`, so your key won't be committed.

### 3. Install dependencies

#### Option A: with uv (recommended)

```bash
pip install uv          # if you don't have it yet
uv sync                 # creates .venv and installs locked dependencies
```

#### Option B: with pip

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install anthropic python-dotenv prompt-toolkit "mcp[cli]>=1.8.0"
```

If you use pip, set `USE_UV=0` in `.env` so the app starts the server with `python`.

---

## Getting started

### Run the app

```bash
# with uv
uv run main.py

# or with an activated virtualenv
python main.py
```

You'll see a `>` prompt. Some things to try:

**1. Ask a normal question**
```
> What documents do you have access to?
```

**2. Mention a document with `@`** (press `@` to open the completion list)
```
> Summarize @deposition.md in one sentence
```

**3. Let Claude use tools**
```
> Read spec.txt and change "equipment" to "hardware"
```
Claude will call `read_doc_contents` and then `edit_document`. Ask it about `@spec.txt` again to see the change.

**4. Run a slash command** (press `/` to list the available commands)
```
> /format plan.md
```

Press **Ctrl+C** to exit.

### Connect more MCP servers

Any extra arguments are treated as MCP server scripts and started with `uv run`:

```bash
uv run main.py my_other_server.py another_server.py
```

Tools from all servers are shown to Claude together, and each call goes to the server that provides the tool.

### Inspect the server on its own

The `mcp[cli]` extra includes the **MCP Inspector**, a web UI for trying tools, resources, and prompts without the LLM:

```bash
uv run mcp dev mcp_server.py
```

You can also run the client file directly for a quick check that lists the server's tools:

```bash
uv run mcp_client.py
```

---

## Extending the project

**Add documents.** Add entries to the `docs` dictionary in `mcp_server.py`:

```python
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "notes.txt": "Your new document content here.",
}
```

**Add a tool.** Decorate a function with `@mcp.tool`. Its type hints and `Field` descriptions become the input schema that Claude sees:

```python
@mcp.tool(name="word_count", description="Counts the words in a document")
def word_count(doc_id: str = Field(description="Id of the document")) -> int:
    return len(docs[doc_id].split())
```

**Add a slash command.** Decorate a function with `@mcp.prompt`. It appears in the CLI as `/<name>` automatically:

```python
@mcp.prompt(name="summarize", description="Summarizes a document")
def summarize(doc_id: str = Field(description="Id of the document")) -> list[base.Message]:
    return [base.UserMessage(f"Summarize the document with id {doc_id}. Use read_doc_contents to read it.")]
```

---

## Roadmap

- [ ] `/summarize` prompt for documents
- [ ] Persist documents to disk instead of keeping them in memory
- [ ] Stream Claude's responses token by token
- [ ] Linting, type checking, and tests

---

## Learn more

- [Model Context Protocol documentation](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anthropic tool use guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
