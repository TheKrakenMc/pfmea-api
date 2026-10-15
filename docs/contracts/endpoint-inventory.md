# Endpoint authorization inventory

Generated from registered OpenAPI routes. Each private route is tested anonymously; every private write is tested with Viewer. Resource isolation, revisions and business validation have additional targeted regressions.

| Method | Endpoint | Authorization / integrity | Tests |
|---|---|---|---|
| GET | /api/v1/auth/me | Active authenticated account; persisted session; CSRF for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/auth/login | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| POST | /api/v1/auth/refresh | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| POST | /api/v1/auth/logout | Active authenticated account; persisted session; CSRF for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/auth/verify-email | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| POST | /api/v1/auth/change-password | Active authenticated account; persisted session; CSRF for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/auth/forgot-password | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| POST | /api/v1/auth/reset-password | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| GET | /api/v1/auth/csrf | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| POST | /api/v1/users/register | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/users/lookup | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/users/ | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/users/admin | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/users/{user_id} | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/users/{user_id}/role | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/users/{user_id}/status | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/users/{user_id}/resend-verification | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/users/{user_id}/plants | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/users/{user_id}/plants | Administrator; server-resolved actor and plant assignments | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/flowcharts/ | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/flowcharts/ | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/flowcharts/products | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/flowcharts/products | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/flowcharts/{flowchart_id} | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/flowcharts/{flowchart_id} | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/flowcharts/{flowchart_id}/steps | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/flowcharts/{flowchart_id}/steps | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PATCH | /api/v1/flowcharts/{flowchart_id}/archive | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/flowcharts/{flowchart_id}/history | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/flowcharts/{flowchart_id}/save | Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/document-versions/ | Authorization resolved through source document; server-generated snapshots | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/document-versions/{document_type}/{document_id} | Authorization resolved through source document; server-generated snapshots | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/document-versions/{version_id} | Authorization resolved through source document; server-generated snapshots | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/ | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/ | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/my-tasks | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/ap-lookup | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/{pfmea_id} | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/pfmea-project/{pfmea_id} | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PATCH | /api/v1/pfmea-project/{pfmea_id}/status | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/{pfmea_id}/restore | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/{pfmea_id}/sync-flowchart | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/{pfmea_id}/team | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/pfmea-project/{pfmea_id}/team/{member_id} | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/{pfmea_id}/worksheet | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/{pfmea_id}/worksheet | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PATCH | /api/v1/pfmea-project/{pfmea_id}/worksheet/{row_id} | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/pfmea-project/{pfmea_id}/worksheet/{row_id} | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/pfmea-project/{pfmea_id}/worksheet/bulk | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/pfmea-project/{pfmea_id}/audit-log | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/pfmea-project/{pfmea_id}/worksheet/{row_id}/confirm-action | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/pfmea-project/{pfmea_id}/save | Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/control-plans/project/{pfmea_id} | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/control-plans/project/{pfmea_id} | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/control-plans/{control_plan_id}/sync-from-pfmea | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/control-plans/items/{item_id} | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/control-plans/ | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| PATCH | /api/v1/control-plans/{control_plan_id}/status | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/control-plans/items/{item_id}/review-source | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/control-plans/{control_plan_id}/restore | Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/products/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/products/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/products/{product_id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/products/{product_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/products/{product_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/products/{product_id}/status | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/products/{product_id}/revisions | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/products/{product_id}/history | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/products/upload-image | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/products/images/{plant_id}/{filename} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/products/{product_id}/parameters | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/products/{product_id}/parameters | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/products/parameters/{param_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/products/parameters/{param_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/products/{product_id}/parameters/bulk | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/technologies/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/technologies/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/technologies/{tech_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/technologies/{tech_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/technologies/{tech_id}/impact | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/technologies/{tech_id}/parameters | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/technologies/{tech_id}/parameters | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/technologies/parameters/{param_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/technologies/parameters/{param_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/technology-categories/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/technology-categories/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/technology-categories/{category_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/technology-categories/{category_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/customers/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/customers/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/customers/{customer_id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/customers/{customer_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/customers/{customer_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/machinery/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/machinery/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/machinery/{id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/machinery/{id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/machinery/{id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/plants/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/manufacturing_locations/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/manufacturing_locations/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/manufacturing_locations/{location_id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/manufacturing_locations/{location_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/manufacturing_locations/{location_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/product-families/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/product-families/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/product-families/{family_id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/product-families/{family_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/product-families/{family_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/production-lines/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/production-lines/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/production-lines/{line_id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/production-lines/{line_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/production-lines/{line_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/departments/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/departments/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/departments/{department_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/departments/{department_id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/measurement-units/ | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| POST | /api/v1/measurement-units/ | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/measurement-units/{id} | Authenticated authorized plant/catalog; parent resources checked for child IDs | test_security.py; test_audit_regressions.py; test_integrity.py |
| PUT | /api/v1/measurement-units/{id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| DELETE | /api/v1/measurement-units/{id} | Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs | test_security.py; test_audit_regressions.py; test_integrity.py |
| GET | /api/v1/health | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
| GET | /api/v1/readiness | Public; purpose-bound credentials/rate limits where applicable | test_security.py; test_auth.py |
