# Revisión de trazabilidad del alcance aprobado

| Concepto | Entidad existente | Integridad |
|---|---|---|
| Producto / parte | products | Planta, revisión e historial |
| Diagrama / operación | flowcharts / flowchart_steps | ID estable, orden y suboperación |
| Riesgo | pfmea_headers / pfmea_worksheet_rows | Paso de origen, AP provisional y cierre validado |
| Control | control_plans / control_plan_items | FK a fila PFMEA y source_row_id conservado al eliminar la fuente |
| Revisión | document_versions | Snapshot de servidor al aprobar y antes de reabrir |
| Cambio | document_audit_logs | Actor real, valores anteriores/nuevos y misma transacción |
| Hallazgo de origen | needs_review / source_reviewed / source_review_reason | Revisión humana de vínculos históricos o ambiguos |

Confirmado por código y fixtures sintéticos: renombrar no cambia identidad; reducir riesgo no borra controles; eliminar una fila conserva su procedencia; cerrar acciones exige evidencia y validación del Owner.

Decisión humana del plan: control generado único por plan y fila PFMEA. Es una decisión de esta aplicación, no una correspondencia normativa universal uno a uno. Varios controles por causa o característica requerirían ampliar el contrato posteriormente.

AP: Python es referencia provisional; se verifica paridad de 1.000 combinaciones. El umbral acordado es AP H o S ≥ 9. No se declara conformidad con tablas licenciadas ni certificación AIAG/VDA.

No evaluable en esta ejecución: APQP, PPAP, MSA, SPC, Safe Launch y requisitos específicos de cliente. No se importaron libros Excel ni documentos externos. No se desarrolló un módulo de instrucciones. La referencia P703 de la skill sólo aportó criterios de revisión; sus archivos no fueron auditados aquí.

Las migraciones son aditivas. La reversión operativa restaura el respaldo ensayado; no se incluye un down destructivo que elimine nuevas evidencias, sesiones o revisiones.
