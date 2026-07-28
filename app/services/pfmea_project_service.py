"""PFMEA project service — delegates to pfmea_service for all business logic."""

# Re-export everything from the new service module for backward compatibility.
from app.services.pfmea_service import (  # noqa: F401
    create_pfmea_analysis,
    get_pfmea_analysis,
    list_pfmea_analyses,
    update_pfmea_header,
    add_team_member,
    remove_team_member,
    sync_worksheet_from_flowchart,
    get_worksheet_rows,
    create_worksheet_row,
    update_worksheet_row,
    delete_worksheet_row,
    transition_moc_status,
    restore_to_draft,
    get_pfmea_audit_log,
    get_my_tasks,
    ap_lookup,
)
