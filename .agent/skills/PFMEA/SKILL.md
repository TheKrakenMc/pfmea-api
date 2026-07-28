### Paso 1: Planeación y Preparación (Planning and Preparation)
* **Objetivo:** Acotar los límites del análisis, identificar las fronteras tecnológicas del proyecto y asentar las bases del equipo multidisciplinario (Core Team).
* **Lógica de Control:** Inicializa el contenedor del análisis en la base de datos mediante la generación de la **Cabecera Global Única**. Establece las variables estáticas del entorno de manufactura (Planta, Línea, Cliente, Números de Parte).
* **Regla de Negocio:** Ningún usuario o proceso puede instanciar pasos posteriores si el ID jerárquico estandarizado (`[Planta]_PFMEA_[NumAnalisis]_[Año]_[Versión]`) no ha sido validado como único e inmutable en el backend.

### Paso 2: Análisis de Estructura (Structure Analysis)
* **Objetivo:** Desglosar el proceso de manufactura en límites físicos y lógicos operacionales legibles por el sistema a través de tres niveles de abstracción:
  1. **Elemento de Proceso Superior (System):** El ecosistema industrial global o línea completa (ej. *Línea de Ensamble de Chasis - Planta Saltillo*).
  2. **Elemento de Enfoque (Focus Element):** La estación de trabajo específica que se somete a escrutinio directo. Este campo es heredado automáticamente y en tiempo real desde los nodos guardados en el módulo del **Flowchart** (ej. *Operación 30: Aplicación de Adhesivo Estructural*).
  3. **Elemento de Trabajo del Proceso (Process Work Element - 4M):** Los catalizadores u objetos específicos que interactúan en la estación bajo la categorización obligatoria de las 4M industriales (*Mano de obra, Maquinaria/Herramental, Material, Medio Ambiente*).
* **Validación de Integridad:** El backend rechazará cualquier intento de crear funciones en el Paso 3 si el Elemento de Enfoque seleccionado carece de al menos un elemento de trabajo de la categoría 4M asignado en la base de datos.

### Paso 3: Análisis de Función (Function Analysis)
* **Objetivo:** Definir de manera positiva y medible el "deber ser" de cada uno de los niveles estructurales parametrizados en el Paso 2.
  1. **Función del Elemento Superior:** Requerimientos de alto nivel, normativas del cliente o especificaciones de calidad globales (ej. *Garantizar la rigidez estructural del chasis contra impactos laterales según norma APG-04*).
  2. **Función del Elemento de Enfoque:** El entregable directo de la estación de trabajo bajo análisis, detallando tolerancias mecánicas, químicas o físicas (ej. *Depositar un cordón continuo de adhesivo de 5mm ± 0.5mm de diámetro a lo largo del perímetro*).
  3. **Función del Elemento de Trabajo (4M):** El comportamiento esperado o calibración requerida para el recurso específico (ej. *Maquinaria: Mantener la boquilla del robot a una temperatura constante de 60°C y presión de 3 Bar*).

### Paso 4: Análisis de Falla (Failure Analysis)
* **Objetivo:** Identificar las desviaciones negativas u omisiones de las funciones declaradas en el Paso 3, construyendo una cadena de fallas con relaciones lógicas de causa y efecto.
  1. **Efecto de Falla (Failure Effect - FE):** Las consecuencias directas de la falla experimentadas en el elemento superior, en la planta de ensamble subsiguiente o por el usuario final (ej. *Pérdida de adherencia estructural / Desprendimiento de panel en prueba de impacto / Reclamación de Cliente con penalización tipo IATF*).
  2. **Modo de Falla (Failure Mode - FM):** La manera física o lógica en la que el Elemento de Enfoque no cumple con su especificación (ej. *Cordón de adhesivo interrumpido o con diámetro menor a 4.5mm*).
  3. **Causa de Falla (Failure Cause - FC):** La razón técnica e inmediata por la cual ocurre el Modo de Falla, asociada unívocamente a una falla en el Elemento de Trabajo de las 4M (ej. *Obstrucción parcial de la boquilla dispensadora por acumulación de material curado*).
* **Regla de Sincronización Aguas Abajo:** Si la Severidad ($S$) dictaminada para el Efecto de Falla en el Paso 5 es mayor o igual a 9 ($S \geq 9$), el motor de backend forzará la activación del flag de **Característica Especial (Critical / Significant Characteristic)** para ese Modo de Falla, inyectando de forma automática este registro como un requerimiento obligatorio en el **Control Plan**.

### Paso 5: Análisis de Riesgo (Risk Analysis)
* **Objetivo:** Evaluar la magnitud del riesgo técnico actual mediante la asignación de tres métricas cuantitativas e identificar el nivel de urgencia de intervención a través de la Prioridad de Acción (AP).
* **Métricas Operativas:**
  * **Severidad (S):** Gravedad del Efecto de Falla ($1$ al $10$). Inmutable ante cambios de controles locales; solo decrece mediante rediseño del producto o proceso global.
  * **Controles Actuales de Prevención (PC):** Acciones, barreras o instrucciones vigentes en piso que mitigan la probabilidad de que la Causa de Falla ($FC$) llegue a materializarse (ej. *Mantenimiento preventivo quincenal y purga automatizada de boquilla*).
  * **Ocurrencia (O):** Estimación numérica ($1$ al $10$) de la probabilidad de que la causa ocurra ponderando la efectividad real de los controles de prevención actuales.
  * **Controles Actuales de Detección (DC):** Dispositivos ópticos, manuales o estadísticos implementados en la estación para identificar el Modo de Falla ($FM$) o la Causa de Falla ($FC$) antes de que la pieza abandone la línea o pase a la siguiente estación (ej. *Sistema de visión artificial Cognex que escanea el 100% de la trayectoria del adhesivo*).
  * **Detección (D):** Capacidad de los controles vigentes para descubrir la falla antes del escape ($1$ al $10$, donde 1 es detección garantizada y 10 es nula).
* **Motor de Indexación AP (Action Priority):** El sistema **excluye por completo** el cálculo tradicional del RPN ($S \times O \times D$). En su lugar, implementa un motor de búsqueda indexada en base de datos que evalúa la combinación exacta de las tuplas $(S, O, D)$ contra las tablas normalizadas de la metodología AIAG-VDA 2019, clasificando el riesgo en tres niveles de Prioridad de Acción:
  * **Alta (H - High):** Revisión y optimización mandatoria. Obliga al equipo a definir acciones correctivas inmediatas.
  * **Media (M - Medium):** Revisión recomendada. El equipo debe evaluar controles adicionales para reducir el riesgo.
  * **Baja (L - Low):** Riesgo aceptable bajo las condiciones y controles actuales del proceso.

### Paso 6: Optimización (Optimization)
* **Objetivo:** Diseñar, ejecutar y validar acciones técnicas orientadas a robustecer el proceso, disminuyendo los índices de Ocurrencia y Detección para mitigar los riesgos evaluados con AP Alta (H) o Media (M).
* **Lógica del Workdflow:**
  * Cada acción recomendada debe poseer un ID de responsable válido y una fecha de compromiso explícita.
  * **Estados de la Acción:** `Open` -> `In Progress` -> `Completed` o `Justified`.
  * Tras la implementación de la acción con su debida evidencia registrada, el *PFMEA Owner* introduce la re-evaluación del riesgo: Nuevos valores para Ocurrencia Residual y Detección Residual, lo que recalcula en tiempo real la **AP Residual**.
* **Filtro de Seguridad (Gatekeeper):** El motor de ciclo de vida del documento bloqueará de forma nativa la transición del estado del análisis a `Approved` si existe una sola fila con Prioridad de Acción Inicial Alta ($AP = H$) cuyo estatus en la sección de Optimización permanezca como `Open` o `In Progress` sin un campo de justificación técnica formalizado.

### Paso 7: Comunicación e Informe (Results Documentation)
* **Objetivo:** Consolidar, estructurar y exportar las conclusiones del análisis de riesgos para auditorías internas de calidad, requerimientos del cliente (PPAP) o revisiones del corporativo bajo esquemas IATF 16949 y TISAX.
* **Automatización del Sistema:** Al adquirir el estado `Approved`, el software libera los módulos de descarga. Genera de forma nativa la matriz de distribución de riesgos, comparando el volumen de filas con estatus AP Alto, Medio y Bajo antes y después de la fase de optimización para demostrar de manera cuantitativa el incremento en la confiabilidad de la planta.

---

## 3. Arquitectura de Datos Unificada: Esquema JSON

Para garantizar la interoperabilidad sin fricciones entre la interfaz web en React (frontend) y los endpoints asíncronos en FastAPI (backend), la información de las worksheets del PFMEA se modela bajo el siguiente esquema JSON unificado y fuertemente tipado.

### 3.1. Estructura Completa del Payload del Análisis (GET / PUT / POST)

Este esquema representa la carga de datos completa para un renglón del análisis de riesgos, consolidando los 7 pasos técnicos definidos por el estándar internacional.

```json
{
  "analysis_metadata": {
    "analysis_id": "SALTILLO_PFMEA_024_2026_V1",
    "plant_location": "SALTILLO",
    "document_number": "024",
    "year": 2026,
    "version": "1",
    "status": "Under Review",
    "project_name": "Plataforma EV NexGen",
    "customer": "APG Automotive NA",
    "original_release_date": "2026-02-15T08:00:00Z",
    "moc_status": "ACTIVE_REVISION",
    "part_number": "APG-8832-X2",
    "product_description": "Soporte de Batería Estructural de Aluminio",
    "product_family": "EV_Structural_Components",
    "production_line": "Línea de Ensamble de Chasis B",
    "pfmea_owner_id": "ENG_4509",
    "core_team_ids": ["ENG_4509", "QA_1102", "MAINT_9982", "LOG_3341"]
  },
  "worksheet_row": {
    "row_id": "ROW_024_0034_A",
    "sequence_number": 34,
    "step_2_structure_analysis": {
      "higher_level_system": "Línea de Ensamble de Chasis B - Planta Saltillo",
      "focus_element_operation": "Operación 30: Aplicación de Adhesivo Estructural",
      "work_element_4m": {
        "category": "Maquinaria",
        "description": "Robot KUKA KR16 con celda de dispensado termo-controlada",
        "asset_id": "ROB-KUKA-30B"
      }
    },
    "step_3_function_analysis": {
      "higher_level_function": "Garantizar la rigidez estructural del chasis contra impactos laterales según norma APG-04",
      "focus_element_function": "Depositar un cordón continuo de adhesivo de 5mm ± 0.5mm de diámetro a lo largo del perímetro del soporte",
      "work_element_function": "Mantener la boquilla del robot dispensador a una temperatura constante de 60°C ± 2°C y una presión hidráulica estable de 3 Bar"
    },
    "step_4_failure_analysis": {
      "failure_effect_fe": {
        "description": "Pérdida de adherencia estructural / Desprendimiento potencial de panel en prueba de choque / Riesgo de seguridad para usuario final",
        "affects_customer": true,
        "affects_plant": false
      },
      "failure_mode_fm": {
        "description": "Cordón de adhesivo interrumpido o con diámetro menor a la especificación (< 4.5mm)",
        "is_special_characteristic": true,
        "characteristic_class": "Critical (CC)"
      },
      "failure_cause_fc": {
        "description": "Obstrucción parcial de la boquilla dispensadora por acumulación de material remanente curado",
        "root_4m_link": "Maquinaria"
      }
    },
    "step_5_risk_analysis": {
      "severity": 9,
      "current_prevention_controls": [
        "Mantenimiento preventivo quincenal a los sellos de la boquilla",
        "Purga automatizada del sistema dispensador tras 10 minutos de inactividad de línea"
      ],
      "occurrence": 4,
      "current_detection_controls": [
        "Inspección visual por atributos realizada por el operador una vez por turno al arrancar",
        "Sistema de visión artificial Cognex In-Sight en tiempo real acoplado a la trayectoria del robot"
      ],
      "detection": 3,
      "action_priority_calculated": "H"
    },
    "step_6_optimization": {
      "recommended_action": "Implementar un interbloqueo electrónico de paro de línea automatizado (Poka-Yoke) conectado al sistema Cognex que bloquee el ciclo de la estación si detecta una discontinuidad en la trayectoria",
      "action_type": "Mitigación por Detección/Prevención Automatizada",
      "assignee_id": "QA_1102",
      "assignee_name": "Ing. Carlos Mendoza",
      "target_due_date": "2026-09-15",
      "action_status": "In Progress",
      "action_taken_evidence": null,
      "actual_completion_date": null,
      "residual_risk_evaluation": {
        "residual_severity": 9,
        "residual_occurrence": 4,
        "residual_detection": 1,
        "residual_action_priority_calculated": "L"
      }
    },
    "audit_trail": {
      "created_by": "ENG_4509",
      "created_at": "2026-06-01T14:23:11Z",
      "last_modified_by": "QA_1102",
      "last_modified_at": "2026-06-08T10:15:44Z"
    }
  }
}