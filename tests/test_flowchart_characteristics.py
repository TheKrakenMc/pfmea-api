from app.models.flowchart_step import FlowchartStep
from app.schemas.flowchart import FlowchartStepCreate


def test_flowchart_step_schema_characteristics():
    payload = FlowchartStepCreate(
        step_number=10,
        sub_step=1,
        product_characteristics="Dimensions 100x50mm",
        process_characteristics="Temperature 180C",
        target="Zero burrs",
    )
    assert payload.step_number == 10
    assert payload.sub_step == 1
    assert payload.product_characteristics == "Dimensions 100x50mm"
    assert payload.process_characteristics == "Temperature 180C"
    assert payload.target == "Zero burrs"


def test_flowchart_step_model_attributes():
    step = FlowchartStep(
        step_number=20,
        sub_step=0,
        symbol_type="operation",
        product_characteristics="Crash pad",
        process_characteristics="Clips engaged",
        target="Properly fixed",
    )
    assert step.step_number == 20
    assert step.sub_step == 0
    assert step.product_characteristics == "Crash pad"
    assert step.target == "Properly fixed"


def test_function_process_step_merge_logic():
    prod = "Crash pad"
    target = "Properly fixed"
    merged = []
    if prod and prod.strip():
        merged.append(f"- {prod.strip()}")
    if target and target.strip():
        merged.append(target.strip())
    result = "\n".join(merged)
    assert result == "- Crash pad\nProperly fixed"
