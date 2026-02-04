"""FastAPI entrypoint exposing the unified KakoAI agent and HTTP API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import dspy
from fastapi import FastAPI, Depends, Form, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tempfile
import os

from backend.src.config import GEMINI_2_5_FLASH, AVAILABLE_MODELS, MODEL_OPTIONS
from backend.src.agent import KakoAgent
from backend.src.models import (
    AgentRequest,
    AgentResponse,
    TextBlock,
    ToolUseBlock,
    BillOfMaterials,
)
from backend.src.utils import (
    extract_tool_calls_from_trajectory,
    build_bom_tool_block,
    build_procurement_tool_block,
    build_cost_analysis_tool_block,
    append_to_history,
    compute_bom_id,
    apply_bom_update,
)

## --- Configure LLM globally ---
## 1. Save the original request method
## We patch the class's __call__ method because instance-level patching of __call__ doesn't work for dunder methods,
## and basic_request appears to be missing in this version of DSPy.
#LMClass = type(GEMINI_2_5_FLASH)
#original_call = LMClass.__call__
#
## 2. Define the "Spy" function
#def verbose_call_spy(self, *args, **kwargs):
#    """
#    Wraps the LLM request to print the Agent's 'Thoughts' in real-time.
#    """
#    # (Optional) Print the Prompt to see what the agent is seeing
#    prompt_or_messages = kwargs.get("messages") or kwargs.get("prompt") or (args[0] if args else "Unknown")
#    import pprint
#    print(f"\n📩 [SENDING PROMPT/MESSAGES]:")
#    if isinstance(prompt_or_messages, list):
#        for msg in prompt_or_messages:
#            print(msg)
#    else:
#        print(prompt_or_messages)
#    print("-" * 20 + "\n")
#
#    # Execute the actual API call
#    completions = original_call(self, *args, **kwargs)
#    
#    # Print the Agent's immediate response (The "Thought")
#    # completions is usually a list of strings or dicts in DSPy
#    for i, c in enumerate(completions):
#        # Handle simple string or object response
#        text = c if isinstance(c, str) else str(c)
#        print(f"\n🧠 [AGENT THOUGHT]:\n{text}\n{'='*40}")
#        
#    return completions
#
## 3. Apply the patch
#print("🕵️♂️ Injection: Real-time Thought Spy activated (Class Level, Kwargs Support).")
#LMClass.__call__ = verbose_call_spy
#
dspy.configure(lm=GEMINI_2_5_FLASH)

app = FastAPI(title="KakoAI")

# Allow local frontend (Vite) to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve temporary files (for generated images/PDFs)
temp_dir = tempfile.gettempdir()
print(f"Mounting static files from: {temp_dir}")
app.mount("/files", StaticFiles(directory=temp_dir), name="files")

# Instantiate the unified agent once and store on app state for DI access
app.state.agent = KakoAgent()
app.state.histories = {}
app.state.boms = {}


def get_agent(request: Request) -> KakoAgent:
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        print("Agent not initialized, creating new instance..")
        agent = KakoAgent()
        request.app.state.agent = agent
    return agent


def _get_history_for_thread(thread_id: str | None) -> dspy.History:
    """Return a per-thread DSPy History (in-memory)."""
    # For MVP: in-memory, single-process storage. If thread_id is missing, use a shared default.
    # For production, use explicit thread IDs + an external store (Redis/DB).
    tid = thread_id or "default"
    histories = app.state.histories
    history = histories.get(tid)
    if history is None:
        history = dspy.History(messages=[])
        histories[tid] = history
    return history


@app.post("/agent", response_model=AgentResponse)
async def run_agent(
        request: Request,
        user_query: str | None = Form(
            default=None, description="Natural language request to complete."
        ),
        thread_id: str | None = Form(default=None),
        model_id: str | None = Form(default=None),
        file: UploadFile | None = File(default=None),
        agent: KakoAgent = Depends(get_agent),
) -> AgentResponse:
    """Unified agent endpoint returning blocks the frontend can render.

    Accepts form-encoded `user_query` and optional `file`.
    JSON body is supported ONLY if no file is uploaded (via manual parsing fallback).
    """
    
    bom_update = None

    # Handle JSON fallback if CONTENT_TYPE is application/json
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = AgentRequest.model_validate(await request.json())
            user_query = payload.user_query
            thread_id = payload.thread_id
            bom_update = payload.bom_update
            model_id = payload.model_id
        except Exception:
             pass # Will fall through to form check

    if user_query is None:
         raise HTTPException(
            status_code=400,
            detail="Missing `user_query` (expected form field or JSON body).",
        )

    file_path = None
    if file:
        try:
            suffix = os.path.splitext(file.filename or "")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file_path = tmp.name
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())
            
            # Injection: Append the file location so the agent can use the path directly.
            user_query += f" (file_path: '{file_path}')"
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save uploaded file: {e}",
            )

    thread_key = thread_id or "default"
    history = _get_history_for_thread(thread_key)

    # Apply user-confirmed BOM edits (if provided) before running the agent.
    if bom_update is not None:
        stored = app.state.boms.get(thread_key)
        if not stored or stored.get("bom_id") != bom_update.bom_id:
            raise HTTPException(
                status_code=409,
                detail="BOM revision mismatch; please refresh and confirm again.",
            )
        merged = apply_bom_update(stored["bom"], bom_update)
        
        # 1. Update app state (for UI / History)
        app.state.boms[thread_key] = {
            "bom_id": stored["bom_id"],
            "bom": merged,
            "source_document": stored.get("source_document"),
        }
        
        # 2. Update BOMStore (Single Source of Truth for Agent Tools)
        from backend.src.store import BOMStore
        BOMStore().save_bom(stored["bom_id"], merged, source_document=stored.get("source_document") or "")
        print(f"--- [Main] Synced User Edits to BOMStore ID: {stored['bom_id']} ---")

        append_to_history(
            history,
            user_query="__BOM_CONFIRMED__",
            process_result=merged.model_dump_json(),
        )
        if user_query.strip() == "__BOM_CONFIRM__":
            from backend.src.tools.demand_analysis.inventory import xentral_BOM
            result = xentral_BOM(merged)
            return AgentResponse(
                response_id=f"msg_{uuid.uuid4()}",
                created_at=datetime.now(timezone.utc),
                blocks=[TextBlock(content=f"BOM Saved to Xentral.\nStats: {result}")],
            )

    # Select LM based on request or default
    selected_lm = AVAILABLE_MODELS.get(model_id, GEMINI_2_5_FLASH)
    
    # Run the agent with the selected LM context
    with dspy.context(lm=selected_lm):
        prediction = agent(user_query=user_query, history=history)
    
    content = getattr(prediction, "process_result", None) or str(prediction)

    blocks: list[TextBlock | ToolUseBlock] = []
    if content:
        blocks.append(TextBlock(content=content))

    # Convert tool outputs into UI blocks using DSPy's recorded trajectory.
    trajectory = getattr(prediction, "trajectory", None)
    procurement_tools = {
        "filter_sellers_by_shipping",
        "sort_and_filter_by_best_price",
        "search_part_by_mpn",
        "find_alternatives",
        "optimize_order",
    }
    feasibility_tools = {"check_feasibility", "bom_check"}
    for tool_name, tool_args, observation in extract_tool_calls_from_trajectory(trajectory):
        if tool_name in procurement_tools:
            procurement_block = build_procurement_tool_block(observation)
            if procurement_block is not None:
                blocks.append(procurement_block)
            cost_block = build_cost_analysis_tool_block(observation)
            if cost_block is not None:
                blocks.append(cost_block)
            continue
        if tool_name in feasibility_tools:
            blocks.append(
                ToolUseBlock(
                    tool_name="track_feasibility_check",
                    data={"event_id": f"FEAS_{uuid.uuid4().hex[:12].upper()}", "tool": tool_name},
                )
            )
            continue
        if tool_name != "perform_bom_extraction":
            continue

        bom: BillOfMaterials | None = None
        src_image_for_preview: str | None = None
        extracted_id = None  # Capture ID from tool output

        if isinstance(observation, tuple):
            # (bom, used_image_path)
            bom_obj, used_image = observation
            if isinstance(bom_obj, BillOfMaterials):
                bom = bom_obj
                src_image_for_preview = used_image
        elif isinstance(observation, BillOfMaterials):
            bom = observation
        elif isinstance(observation, dict):
            try:
                bom = BillOfMaterials.model_validate(observation)
            except Exception:
                pass
        
        # New: Check for BOM ID in string observation (Hybrid approach)
        elif isinstance(observation, str) and "Reference ID:" in observation:
            import re
            match = re.search(r"Reference ID: (BOM_[A-F0-9]+)", observation)
            if match:
                found_id = match.group(1)
                from backend.src.store import BOMStore
                store = BOMStore()
                stored_entry = store.get_bom(found_id)
                if stored_entry:
                     bom = stored_entry["bom"]
                     src_image_for_preview = stored_entry.get("source_document")
                     extracted_id = found_id  # Use this ID!
                     print(f"--- [Main] Hydrated BOM UI from Store ID: {found_id} ---")
        
        if bom is None:
            continue

        source = tool_args.get("file_path") or tool_args.get("file") or tool_args.get("filename")
        
        # Use extracted ID if available, otherwise fallback to hash
        bom_id = extracted_id if extracted_id else compute_bom_id(bom, source_document=source)
        
        app.state.boms[thread_key] = {"bom_id": bom_id, "bom": bom, "source_document": source}
        
        # Inject detailed history so Agent sees the Data AND the ID
        history_content = f"BOM ID: {bom_id}\nDATA: {bom.model_dump_json()}"
        append_to_history(history, user_query=f"System: BOM Extraction Completed (ID: {bom_id})", process_result=history_content)
        
        blocks.append(
            build_bom_tool_block(
                bom, 
                source_document=source, 
                preview_image=src_image_for_preview, 
                bom_id=bom_id, 
                thread_id=thread_key
            )
        )

    append_to_history(history, user_query=user_query, process_result=content)
    return AgentResponse(
        response_id=f"msg_{uuid.uuid4()}",
        created_at=datetime.now(timezone.utc),
        blocks=blocks,
    )


@app.post("/chat/title")
async def generate_chat_title(request: AgentRequest):
    """Generates a concise title for a chat thread based on the first user message."""
    try:
        class GenerateTitle(dspy.Signature):
            """Summarize the user message into a short, concise chat title (max 5 words). Language should match the user's message."""
            message = dspy.InputField()
            title = dspy.OutputField()

        title_generator = dspy.Predict(GenerateTitle)
        
        # dynamic model selection (default GEMINI_2_5_FLASH)
        selected_lm = AVAILABLE_MODELS.get(request.model_id, GEMINI_2_5_FLASH)

        with dspy.context(lm=selected_lm):
            prediction = title_generator(message=request.user_query)
            title = prediction.title
            
        return {"title": title}
    except Exception as e:
        print(f"Title generation error: {e}")
        return {"title": request.user_query[:30] + "..."}


@app.get("/config/models")
def get_available_models() -> dict:
    """Return list of available LLMs for configuration."""
    return {"models": MODEL_OPTIONS}


@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn backend.src.main:app --reload
