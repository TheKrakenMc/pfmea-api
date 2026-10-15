# Antigravity Skill: VDA & AIAG Technical Documentation Core Engine

## 1. Propósito y Alcance de la Skill
Esta skill proporciona las directrices de arquitectura de software, reglas de negocio industriales y lógica de backend (FastAPI) y frontend (React/TypeScript) para el sistema de gestión de documentación técnica bajo los estándares automotrices **AIAG & VDA (2019)**, **IATF 16949** y requerimientos de seguridad **TISAX**. 

*Exclusiones Críticas:* Este motor es completamente independiente de sistemas ERP globales (como Project Gulliver) y no maneja interfaces visuales de tipo Kanban, utilizando en su lugar un flujo jerárquico de documentos e hilos relacionales de datos controlados por un motor de **Actividades / Tareas Pendientes (My Tasks)**.

---

## 2. Estructura de Datos Unificada: Cabecera Global (Paso 1)
Para garantizar la consistencia de los datos en toda la jerarquía de ingeniería, el sistema implementa una **Cabecera Global Única** administrada en el Paso 1 (Planeación y Preparación). Cualquier documento perteneciente al mismo número de análisis heredará, referenciará e imprimirá de manera idéntica esta información:

* **Identificador Único del Análisis (ID Jerárquico):** `[Planta]_PFMEA_[NumAnalisis]_[Año]_[Versión]` *(Ej. BOCHUM_PFMEA_001_2026_1)*.
* **Información del Proyecto:** Nombre del proyecto, cliente, fecha de lanzamiento original y estado MOC.
* **Datos del Producto / Proceso:** Número de parte (Part Number), descripción del producto, familia de productos y línea de producción/ensamble asignada.
* **Equipo Multidisciplinario (Core Team):** IDs y nombres de los ingenieros involucrados (Calidad, Manufactura, Logística, Operaciones) con asignación explícita del *PFMEA Owner*.

---

## 3. Jerarquía e Interconexión de Documentos Técnicos
El software debe asegurar un flujo de datos continuo y relacional de extremo a extremo de forma descendente. Los cambios o definiciones aguas arriba deben poblar o actualizar automáticamente los campos correspondientes aguas abajo:

```
[ 1. Flowchart ] 
       │
       ▼ (Hereda Operaciones, Estaciones y Elementos 4M)
[ 2. PFMEA ] 
       │
       ▼ (Hereda Características Especiales, Controles de Prevención/Detección)
[ 3. Control Plan ] 
       │
       ▼ (Hereda Parámetros del Proceso, Frecuencias y Métodos de Reacción)
[ 4. Operation Instruction Sheet (OIS) ]
```

### 3.1. Módulo del Diagrama de Flujo de Proceso (Flowchart)
* **Operación / Estación:** Cada nodo del Flowchart representa un paso específico del proceso (ej. Operación 10: Inyección de Plástico).
* **Tipos de Operación:** Clasificación obligatoria del nodo en la interfaz gráfica (Operación de Valor Agregado, Transporte, Almacenamiento, Inspección o Retrabajo).
* **Elementos de Trabajo del Proceso (4M):** El usuario asocia a cada nodo los recursos requeridos (Mano de obra, Maquinaria, Materiales, Medio Ambiente) definidos en el Paso 2 de la metodología.
* *Lógica de Sincronización:* Al guardar o actualizar el Flowchart, el backend creará automáticamente las filas correspondientes en la estructura tabular del PFMEA.

### 3.2. Módulo de Análisis de Modos y Efectos de Falla de Proceso (PFMEA)
* Consume directamente la estructura de operaciones del Flowchart.
* Ejecuta el análisis de los 7 pasos (Estructura, Función, Fallas, Riesgos con cálculo automático de Prioridad de Acción **AP: H/M/L** mediante matriz de búsqueda indexada, Optimización y Comunicación).
* Identifica y etiqueta las **Características Especiales (Critical / Significant Characteristics)** basándose en los Efectos de Falla (FE) con Severidades elevadas ($S \geq 9$).

### 3.3. Módulo del Plan de Control (Control Plan)
* **Derivación Directa:** El sistema debe pre-poblar el Control Plan extrayendo las operaciones del Flowchart y los Controles Actuales de Prevención/Detección aprobados en el PFMEA.
* **Especificaciones Técnicas:** Vincula la característica especial, las tolerancias del producto/proceso, los sistemas de medición del operador, el tamaño y frecuencia de la muestra, y el **Plan de Reacción** ante desviaciones.

### 3.4. Hoja de Instrucción de Operación (Operation Instruction Sheet - OIS)
* **Nivel de Piso:** Documento final que lee el operador en la línea de producción.
* **Lógica de Integración:** El sistema genera plantillas de instrucciones mapeando los parámetros de control del proceso y los métodos de reacción estipulados en el Control Plan para esa estación específica. Garantiza que el operador controle exactamente lo que el equipo multidisciplinario dictaminó en el PFMEA.

---

## 4. Matriz de Roles y Seguridad TISAX
El acceso al sistema se restringe por asignación específica por proyecto para evitar la alteración no autorizada de datos de manufactura confidenciales.

| Rol | Crear Análisis | Editar Hojas de Trabajo | Enviar a Revisión | Autorizar Estados | Funciones Especiales |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Administrator** | X | X | X | X | Restauración de versiones en el Audit Trail y revocación inmediata de cuentas. |
| **PFMEA Owner** | X | X | X | X | Duplicar análisis, crear plantillas con base en documentos aprobados. |
| **Team Member** | | X | X | | Editar worksheets y agregar comentarios en los proyectos asignados. |
| **Viewer** | | | | | Solo lectura a través de toda la jerarquía de documentos. |

*Bajas de Personal:* Si un usuario es marcado como inactivo, el frontend sustituirá dinámicamente su nombre en los históricos por la etiqueta `ARCHIVED [Nombre]` (ej. *ARCHIVED Klaudia Ochojska*) inhabilitando sus credenciales pero reteniendo la integridad de los logs de auditoría.

---

## 5. Ciclo de Vida del Documento y Reglas de Negocio
El estatus del documento es global para el ID jerárquico del análisis (`Draft` -> `Under Review` -> `Approved` -> `Archived`).

* **Validación de Cierre (Gatekeeper):** El sistema **bloqueará** el cambio de estado a `Approved` si alguna fila del PFMEA posee una Prioridad de Acción Alta (AP: H) que no tenga una acción correctiva cerrada o justificada en el paso de Optimización.
* **Generación de Plantillas:** Al pasar a `Approved`, los Pasos 2 al 5 del PFMEA se copian a la tabla de catálogos como plantilla reutilizable, generando un ID único prefijado con `Template_`.
* **Exportación Controlada:** Las opciones de exportación (Generar PDF del análisis, Excel de las worksheets y PNG del Flowchart) estarán deshabilitadas hasta que el documento adquiera el estatus `Approved`.

---

## 6. Control de Cambios (MOC) y Audit Trail
* **Request for Change:** Para editar cualquier documento dentro de un análisis en estado `Approved`, el *PFMEA Owner* debe iniciar una solicitud de cambio. El sistema incrementará de inmediato el dígito de versión en la Cabecera Global, duplicará el contenido hacia un nuevo espacio de trabajo en estado `Draft` e iniciará el registro histórico.
* **Audit Trail Inmutable:** El backend guardará de forma obligatoria los registros de cada operación (INSERT, UPDATE, DELETE), el usuario responsable, la marca de tiempo, el campo alterado, y los valores anterior y nuevo.
* **Vista Side-by-Side:** El frontend en React debe proveer una interfaz comparativa de pantalla dividida para evaluar los cambios de contenido entre dos versiones consecutivas del documento.

---

## 7. Automatizaciones de Monitoreo
* **My Tasks:** Bandeja unificada en el frontend para cada usuario que despliega las acciones pendientes de validación, firmas electrónicas o tareas de optimización asignadas con fecha compromiso.
* **Revisión Anual Automática:** Un proceso en segundo plano (*cron job*) se ejecutará diariamente. Si un análisis cumple 365 días en estado `Approved`, emitirá de manera automática una tarea de alta prioridad en la bandeja *My Tasks* del *PFMEA Owner* exigiendo la revisión y re-certificación del documento frente al estado actual de la línea de producción.
