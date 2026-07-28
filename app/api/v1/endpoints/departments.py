from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentRead
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[DepartmentRead], summary="List all departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Returns a list of all active departments."""
    stmt = select(Department).where(Department.is_active == True).order_by(Department.name.asc())
    res = await db.execute(stmt)
    departments = res.scalars().all()
    return departments


@router.post("/", response_model=DepartmentRead, summary="Create a new department")
async def create_department(
    department_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new department."""
    stmt = select(Department).where(func.lower(Department.name) == department_in.name.lower())
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department with this name already exists",
        )

    department = Department(name=department_in.name)
    db.add(department)
    await db.flush()
    return department


@router.put("/{department_id}", response_model=DepartmentRead, summary="Update a department")
async def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a department by ID."""
    stmt = select(Department).where(Department.id == department_id)
    res = await db.execute(stmt)
    department = res.scalars().first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    if department_in.name is not None:
        # Check uniqueness if name changed
        if department_in.name.lower() != department.name.lower():
            dup_stmt = select(Department).where(func.lower(Department.name) == department_in.name.lower())
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department with this name already exists",
                )
        department.name = department_in.name

    if department_in.is_active is not None:
        department.is_active = department_in.is_active

    await db.flush()
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a department")
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft delete a department."""
    stmt = select(Department).where(Department.id == department_id)
    res = await db.execute(stmt)
    department = res.scalars().first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    department.soft_delete(user_id=current_user.id)
    await db.flush()
