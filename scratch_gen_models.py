import os

models = [
    "control_point_characteristic",
    "control_plan_reaction",
    "instruction_sheet",
    "instruction_step",
    "instruction_material",
    "instruction_equipment",
    "instruction_safety",
    "instruction_quality_check",
    "process_failure_mode",
    "process_parameter_control",
    "document_approval",
    "technical_document",
    "document_traceability"
]

template = '''from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

class {class_name}(Base, SoftDeleteMixin):
    __tablename__ = "{table_name}"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
'''

def to_pascal(snake):
    return ''.join(word.capitalize() for word in snake.split('_'))

for m in models:
    class_name = to_pascal(m)
    table_name = m + "s"
    # special cases for plural
    if table_name.endswith("ys"):
        table_name = table_name[:-2] + "ies"
    elif table_name.endswith("ss"):
        table_name += "es"
        
    path = f"app/models/{m}.py"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(template.format(class_name=class_name, table_name=table_name))
            
print("Done creating models")
