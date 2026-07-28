from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.product_technology import ProductTechnologyMapping
from app.models.technology import Technology
from app.models.product_parameter import ProductParameter
from app.models.technology_parameter import TechnologyParameter
from app.models.document_version import DocumentVersion
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate,
    ProductParameterCreate,
    ProductParameterUpdate,
)


async def list_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    status_filter: Optional[str] = None,
    customer_id: Optional[int] = None
) -> List[Product]:
    stmt = select(Product).options(
        selectinload(Product.customer),
        selectinload(Product.technologies).selectinload(Technology.parameters),
        selectinload(Product.parameters)
    ).where(Product.is_active == True)

    if q:
        stmt = stmt.where(
            or_(
                Product.part_number.ilike(f"%{q}%"),
                Product.customer_part_number.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%")
            )
        )
    
    if status_filter:
        stmt = stmt.where(Product.status == status_filter)
        
    if customer_id:
        stmt = stmt.where(Product.customer_id == customer_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product:
    stmt = select(Product).options(
        selectinload(Product.customer),
        selectinload(Product.technologies).selectinload(Technology.parameters),
        selectinload(Product.parameters)
    ).where(Product.id == product_id, Product.is_active == True)
    
    result = await db.execute(stmt)
    product = result.scalars().first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    product_dict = payload.model_dump(exclude={"technology_ids"})
    
    if not product_dict.get("plant_id"):
        from app.models.plant import Plant
        stmt = select(Plant.id).where(Plant.is_active == True).limit(1)
        result = await db.execute(stmt)
        default_plant_id = result.scalar()
        if default_plant_id:
            product_dict["plant_id"] = default_plant_id
        else:
            product_dict["plant_id"] = 1  # Fallback if no plants are found
            
    db_product = Product(**product_dict)
    db.add(db_product)
    await db.flush()
    
    if payload.technology_ids:
        for tech_id in payload.technology_ids:
            mapping = ProductTechnologyMapping(
                product_id=db_product.id,
                technology_id=tech_id
            )
            db.add(mapping)
            
            # Auto-copy master parameters
            tech_params_stmt = select(TechnologyParameter).where(TechnologyParameter.technology_id == tech_id, TechnologyParameter.is_active == True)
            tech_params_result = await db.execute(tech_params_stmt)
            for tp in tech_params_result.scalars().all():
                prod_param = ProductParameter(
                    product_id=db_product.id,
                    name=tp.name,
                    measurement_unit_id=tp.measurement_unit_id,
                    technology_id=tech_id,
                    target_value=tp.target_value,
                    min_value=tp.min_value,
                    max_value=tp.max_value,
                    is_critical=tp.is_critical,
                    is_active=True
                )
                db.add(prod_param)
    
    await db.commit()
    await db.refresh(db_product)
    
    return await get_product(db, db_product.id)


async def update_product(db: AsyncSession, product_id: int, payload: ProductUpdate) -> Product:
    db_product = await get_product(db, product_id)
    
    update_data = payload.model_dump(exclude_unset=True, exclude={"technology_ids"})
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    if payload.technology_ids is not None:
        # Get old mappings to see what changed
        old_mappings_stmt = select(ProductTechnologyMapping.technology_id).where(ProductTechnologyMapping.product_id == product_id)
        old_mappings_result = await db.execute(old_mappings_stmt)
        old_tech_ids = set(old_mappings_result.scalars().all())
        new_tech_ids = set(payload.technology_ids)
        
        added_tech_ids = new_tech_ids - old_tech_ids
        removed_tech_ids = old_tech_ids - new_tech_ids

        # Delete old mappings
        del_stmt = delete(ProductTechnologyMapping).where(ProductTechnologyMapping.product_id == product_id)
        await db.execute(del_stmt)
        
        # Insert new mappings
        for tech_id in payload.technology_ids:
            mapping = ProductTechnologyMapping(
                product_id=product_id,
                technology_id=tech_id
            )
            db.add(mapping)
            
        # Handle parameters for removed technologies (soft delete)
        if removed_tech_ids:
            for r_tech_id in removed_tech_ids:
                del_params_stmt = select(ProductParameter).where(ProductParameter.product_id == product_id, ProductParameter.technology_id == r_tech_id)
                del_params_res = await db.execute(del_params_stmt)
                for dp in del_params_res.scalars().all():
                    dp.is_active = False

        # Handle parameters for added technologies (copy fresh)
        if added_tech_ids:
            for a_tech_id in added_tech_ids:
                tech_params_stmt = select(TechnologyParameter).where(TechnologyParameter.technology_id == a_tech_id, TechnologyParameter.is_active == True)
                tech_params_result = await db.execute(tech_params_stmt)
                for tp in tech_params_result.scalars().all():
                    prod_param = ProductParameter(
                        product_id=product_id,
                        name=tp.name,
                        measurement_unit_id=tp.measurement_unit_id,
                        technology_id=a_tech_id,
                        target_value=tp.target_value,
                        min_value=tp.min_value,
                        max_value=tp.max_value,
                        is_critical=tp.is_critical,
                        is_active=True
                    )
                    db.add(prod_param)
            
    await db.commit()
    return await get_product(db, product_id)


async def delete_product(db: AsyncSession, product_id: int) -> None:
    db_product = await get_product(db, product_id)
    db_product.is_active = False
    await db.commit()


async def list_technologies(db: AsyncSession) -> List[Technology]:
    stmt = select(Technology)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ── Product Parameter CRUD ───────────────────────────────────────────────

async def list_parameters(
    db: AsyncSession, product_id: int
) -> List[ProductParameter]:
    """Return all active parameters for a product."""
    await get_product(db, product_id)

    stmt = (
        select(ProductParameter)
        .where(
            ProductParameter.product_id == product_id,
            ProductParameter.is_active == True,
        )
        .order_by(ProductParameter.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_parameter(
    db: AsyncSession,
    product_id: int,
    payload: ProductParameterCreate,
) -> ProductParameter:
    await get_product(db, product_id)

    param = ProductParameter(product_id=product_id, **payload.model_dump())
    db.add(param)
    await db.commit()
    await db.refresh(param)
    return param


async def update_parameter(
    db: AsyncSession,
    param_id: int,
    payload: ProductParameterUpdate,
) -> ProductParameter:
    stmt = select(ProductParameter).where(ProductParameter.id == param_id)
    result = await db.execute(stmt)
    param = result.scalars().first()

    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product parameter not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(param, key, value)

    await db.commit()
    await db.refresh(param)
    return param


async def delete_parameter(db: AsyncSession, param_id: int) -> None:
    stmt = select(ProductParameter).where(ProductParameter.id == param_id)
    result = await db.execute(stmt)
    param = result.scalars().first()

    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product parameter not found",
        )

    param.is_active = False
    await db.commit()

# ── Product Versioning & History ──────────────────────────────────────────

async def update_product_status(
    db: AsyncSession, product_id: int, status_val: str
) -> Product:
    db_product = await get_product(db, product_id)
    db_product.status = status_val
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def create_product_revision(
    db: AsyncSession, product_id: int, user_id: int, change_reason: str, engineering_level: str
) -> DocumentVersion:
    db_product = await get_product(db, product_id)
    
    # Update Product's version and engineering level
    db_product.version += 1
    db_product.engineering_level = engineering_level
    db_product.status = "Draft"
    
    # Snapshot
    from app.schemas.product import ProductDetailRead
    snapshot = ProductDetailRead.model_validate(db_product).model_dump(mode="json")
    
    # Create DocumentVersion
    doc_version = DocumentVersion(
        document_type="product",
        document_id=db_product.id,
        revision_number=db_product.version,
        change_reason=change_reason,
        created_by=user_id,
        original_creation_date=db_product.created_at,
        snapshot_data=snapshot
    )
    db.add(doc_version)
    await db.commit()
    await db.refresh(doc_version)
    return doc_version

async def get_product_history(
    db: AsyncSession, product_id: int
) -> List[DocumentVersion]:
    stmt = (
        select(DocumentVersion)
        .options(selectinload(DocumentVersion.creator))
        .where(
            DocumentVersion.document_type == "product",
            DocumentVersion.document_id == product_id
        )
        .order_by(DocumentVersion.revision_number.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

