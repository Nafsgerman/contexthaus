import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Property, Source, Fact
from app.core.llm import generate, generate_json, FLASH, PRO
from app.core.patcher import patch_section, diff_sections, get_section
from prompts.context_generate import SYSTEM, GENERATE_CONTEXT, PATCH_SECTION, SIGNAL_CHECK
import pypdf
import io

router = APIRouter()


async def extract_text(file: UploadFile) -> str:
    content = await file.read()
    if file.filename.endswith(".pdf"):
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="ignore")


async def check_signal(text: str, property_name: str, address: str) -> dict:
    prompt = SIGNAL_CHECK.format(property_name=f"{property_name} at {address}", content=text[:2000])
    result = await generate_json(prompt=prompt, model=FLASH)
    try:
        return json.loads(result)
    except Exception:
        return {"relevant": True, "reason": "parse error", "section": None}


@router.post("/{property_id}/source")
async def ingest_source(
    property_id: str,
    file: UploadFile = File(...),
    source_type: str = Form(default="email"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    text = await extract_text(file)

    # Skip signal check on first ingest — always process
    if prop.context_md and prop.context_md.strip():
        signal = await check_signal(text, prop.name, prop.address)
        if not signal.get("relevant", True):
            return {"status": "ignored", "reason": signal.get("reason"), "changes": []}
    else:
        signal = {"relevant": True, "section": None}

    source = Source(
        id=str(uuid.uuid4()),
        property_id=property_id,
        filename=file.filename,
        source_type=source_type,
        raw_content=text[:50000],
    )
    db.add(source)
    await db.flush()

    old_md = prop.context_md or ""

    if not old_md.strip():
        sources_text = f"[{source_type.upper()}] {file.filename}:\n{text[:10000]}"
        prompt = GENERATE_CONTEXT.format(
            property_name=prop.name,
            address=prop.address,
            sources=sources_text,
            source_list=file.filename,
        )
        new_md = await generate(prompt=prompt, system=SYSTEM, model=PRO)
    else:
        section = signal.get("section") or "Notes"
        current = get_section(old_md, section) or ""
        patch_prompt = PATCH_SECTION.format(
            section_name=section,
            current_content=current,
            source_name=file.filename,
            new_info=text[:3000],
        )
        new_section_content = await generate(prompt=patch_prompt, system=SYSTEM, model=FLASH)
        new_md = patch_section(old_md, section, new_section_content)

    changes = diff_sections(old_md, new_md)
    prop.context_md = new_md
    await db.commit()

    return {
        "status": "ingested",
        "source_id": source.id,
        "filename": file.filename,
        "section_updated": signal.get("section"),
        "changes": changes,
        "context_md": new_md,
    }


@router.get("/{property_id}/context")
async def get_context(property_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"property_id": property_id, "context_md": prop.context_md}
