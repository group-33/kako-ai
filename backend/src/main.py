"""FastAPI entrypoint exposing the unified KakoAI agent and HTTP API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import dspy
from fastapi import FastAPI, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.src.config import GEMINI_2_5_PRO
from backend.src.agent import KakoAgent
from backend.src.models import (
    AgentResponse,
    TextBlock,
    ToolUseBlock,
    BOMRow,
    BOMTableData,
    BillOfMaterials,
)
from backend.src.tools.bom_extraction.bom_tool import perform_bom_extraction

# --- Configure LLM globally ---
dspy.configure(lm=GEMINI_2_5_PRO)

app = FastAPI(title="KakoAI")

# Allow local frontend (Vite) to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the unified agent once and store on app state for DI access
app.state.agent = KakoAgent()


def get_agent(request: Request) -> KakoAgent:
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        print("Agent not initialized, creating new instance..")
        agent = KakoAgent()
        request.app.state.agent = agent
    return agent


class BOMRequest(BaseModel):
    """Request payload for triggering BOM extraction."""

    filename: str


@app.post("/agent")
async def run_agent(
    user_query: str = Form(..., description="Natural language request to complete."),
    agent: KakoAgent = Depends(get_agent),
):
    return agent(user_query=user_query)


@app.post("/bom", response_model=AgentResponse)
async def extract_bom(payload: BOMRequest) -> AgentResponse:
    """Run BOM extraction and return a component-based response for the frontend."""

    result = perform_bom_extraction(payload.filename)

    response_id = f"msg_{uuid.uuid4()}"
    created_at = datetime.now(timezone.utc)
    blocks: list[TextBlock | ToolUseBlock] = []

    if isinstance(result, BillOfMaterials):
        # 1) Text explanation block
        blocks.append(
            TextBlock(
                content=(
                    "Ich habe die Zeichnung erfolgreich verarbeitet. "
                    "Bitte prüfen Sie die automatisch erkannte Stückliste."
                )
            )
        )

        # 2) BOM table tool-use block
        rows: list[BOMRow] = []
        for idx, item in enumerate(result.items):
            row_id = item.part_number or f"item_{idx+1}"
            component = item.description_of_part or f"Part {item.part_number}"
            description_bits = []
            if item.measurements_in_description:
                description_bits.append(item.measurements_in_description)
            if item.no_of_poles:
                description_bits.append(f"{item.no_of_poles} poles")
            if item.hdm_no:
                description_bits.append(f"HDM {item.hdm_no}")
            description = " | ".join(description_bits) if description_bits else None

            rows.append(
                BOMRow(
                    id=row_id,
                    component=component,
                    quantity=item.quantity,
                    unit="Stk",
                    description=description,
                    confidence_score=None,
                )
            )

        bom_data = BOMTableData(rows=rows, source_document=payload.filename)
        blocks.append(
            ToolUseBlock(
                tool_name="display_bom_table",
                data=bom_data.model_dump(),
            )
        )
    else:
        # Error branch: just surface the message as text.
        blocks.append(TextBlock(content=str(result)))

    return AgentResponse(response_id=response_id, created_at=created_at, blocks=blocks)


@app.get("/health")
def service_health() -> dict:
    """Health check endpoint."""

    return {"status": "healthy", "message": "KakoAI API is up and running"}

# Run with: uvicorn backend.src.main:app --reload
