from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth.dependencies import get_current_admin_user
from core.dependencies import get_db
from models.validation_rule import ValidationRule
from models.request_type import RequestType
from schemas.validation_rule import (
    ValidationRuleCreate,
    ValidationRuleRead,
    ValidationRuleUpdate,
    ValidationRuleExport
)

router = APIRouter(prefix="/validation-rules", tags=["validation-rules"])


@router.post("/", response_model=ValidationRuleRead)
async def create_validation_rule(
    rule: ValidationRuleCreate,
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new validation rule (Admin only)."""
    # Check if rule with same name exists
    existing = await db.execute(
        select(ValidationRule).where(ValidationRule.name == rule.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation rule with name '{rule.name}' already exists"
        )

    db_rule = ValidationRule(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    return db_rule


@router.get("/", response_model=List[ValidationRuleRead])
async def list_validation_rules(
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all validation rules."""
    result = await db.execute(select(ValidationRule))
    return result.scalars().all()


@router.get("/{rule_id}", response_model=ValidationRuleRead)
async def get_validation_rule(
    rule_id: UUID,
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific validation rule."""
    db_rule = await db.get(ValidationRule, rule_id)
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {rule_id} not found"
        )
    return db_rule


@router.put("/{rule_id}", response_model=ValidationRuleRead)
async def update_validation_rule(
    rule_id: UUID,
    rule: ValidationRuleUpdate,
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a validation rule."""
    db_rule = await db.get(ValidationRule, rule_id)
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {rule_id} not found"
        )

    # Update version if rules change
    update_data = rule.model_dump(exclude_unset=True)
    if "rules" in update_data:
        update_data["version"] = db_rule.version + 1

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    await db.commit()
    await db.refresh(db_rule)
    
    return db_rule


@router.post("/{rule_id}/assign/{request_type_id}")
async def assign_rule_to_request_type(
    rule_id: UUID,
    request_type_id: UUID,
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a validation rule to a request type."""
    db_rule = await db.get(ValidationRule, rule_id)
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation rule with ID {rule_id} not found"
        )

    db_request_type = await db.get(RequestType, request_type_id)
    if not db_request_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )

    db_request_type.validation_rules.append(db_rule)
    await db.commit()
    
    return {"status": "success"}