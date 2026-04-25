from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Property
import uuid

router = APIRouter()


class PropertyCreate(BaseModel):
    name: str
    address: str


class PropertyResponse(BaseModel):
    id: str
    name: str
    address: str
    context_md: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PropertyResponse])
async def list_properties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).order_by(Property.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=PropertyResponse)
async def create_property(data: PropertyCreate, db: AsyncSession = Depends(get_db)):
    prop = Property(id=str(uuid.uuid4()), name=data.name, address=data.address)
    db.add(prop)
    await db.commit()
    await db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.delete("/{property_id}")
async def delete_property(property_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    await db.delete(prop)
    await db.commit()
    return {"deleted": property_id}