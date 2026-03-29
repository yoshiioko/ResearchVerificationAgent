# SPEC.md: Multi-Node Research & Verification Agent

## 1. Project Goal
To build a stateful, production-ready AI Agent using **LangGraph** and **PydanticAI**. The agent must gather information via web search and undergo a formal "Critic" phase to verify facts before presenting a final report to the user.

## 2. Technical Stack
* **Package Manager:** `uv` (for speed and environment locking)
* **Orchestration:** `langgraph` (State Machine logic)
* **Logic & Validation:** `pydantic` and `pydantic-ai`
* **Model:** Google Gemini (`gemini-1.5-pro` or `gemini-1.5-flash`)
* **Search Tool:** Tavily API

## 3. Architecture: The State Machine
The agent is defined as a `StateGraph` consisting of the following nodes:

### Nodes
* **`researcher_node`**: Receives the query, calls the `web_search` tool, and updates the state with raw findings.
* **`critic_node`**: Analyzes the research findings. It must return a structured Pydantic object containing:
    * `is_verified`: Boolean (True/False)
    * `critique`: String (Explaining what is missing or incorrect)
    * `suggested_queries`: List of strings (To improve the next search if failed)
* **`compiler_node`**: Finalizes the report into a clean, professional Markdown format once verification passes.

### Edges & Routing
1.  **START** -> `researcher_node`
2.  `researcher_node` -> `critic_node`
3.  **Conditional Logic (The Loop):**
    * If `is_verified == False` AND `attempts < 3`: Route back to `researcher_node`.
    * If `is_verified == True` OR `attempts >= 3`: Route to `compiler_node`.
4.  `compiler_node` -> **END**

## 4. Data Schema (`AgentState`)
The shared state must be a Pydantic class containing:
* `messages`: `list[BaseMessage]` (To track conversation history)
* `raw_research`: `str` (Storage for tool outputs)
* `verification_results`: `dict` (To store the Critic's feedback)
* `iteration_count`: `int` (To prevent infinite loops; incremented each research cycle)

## 5. Implementation Roadmap
1.  **Phase 1: State & Tools**: Define the `AgentState` and the `web_search` tool function.
2.  **Phase 2: Node Logic**: Write the Python functions for the Researcher and Critic. Use Pydantic for the Critic's structured output.
3.  **Phase 3: Graph Construction**: Use `StateGraph` to wire nodes and conditional edges together.
4.  **Phase 4: Persistence**: Add a `MemorySaver` checkpointer so the agent remembers state.

## 6. Constraints & Requirements
* **No Hallucinations:** The Critic node must be prompted to be "harsh" and skeptical.
* **Structured Output:** Use Pydantic models to ensure the LLM returns valid JSON for the Critic's assessment.
* **Logging:** Print the current "Node" to the console during execution so the flow is visible in the PyCharm terminal.