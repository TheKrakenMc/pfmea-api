# PFMEA API

Esta es la API para el proyecto PFMEA, construida utilizando [FastAPI](https://fastapi.tiangolo.com/).

## 🚀 Requisitos Previos

- Python 3.8+ (Recomendado 3.10+)
- Base de Datos (PostgreSQL recomendado)

## 🛠️ Instalación y Configuración

Sigue estos pasos para configurar el entorno de desarrollo y ejecutar la API de forma local.

### 1. Clonar el repositorio y entrar al directorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd pfmea-api
```

### 2. Crear y activar un entorno virtual
**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**En Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno
Asegúrate de tener un archivo `.env` en la raíz del proyecto (puedes basarte en `.env.example`).
Abre el archivo `.env` y configura tus variables de conexión a la base de datos:
```ini
# Ejemplo de contenido en .env
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/nombre_db
```

### 5. Iniciar la API
Para ejecutar el servidor de desarrollo de FastAPI con recarga automática, usa `uvicorn`:
```bash
uvicorn app.main:app --reload
```
La API estará disponible en: `http://127.0.0.1:8000`

---

## 📚 Documentación de la API

Dado que esta API está construida con FastAPI, la documentación interactiva se genera automáticamente. 
Una vez que el servidor esté corriendo, puedes acceder a:

- **Swagger UI (Ideal para probar los endpoints):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc (Ideal para leer la especificación):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Referencia Manual de Endpoints

*(Esta sección está preparada para que agregues detalles técnicos adicionales, arquitectura, modelos de datos clave, o la documentación manual de tus rutas a medida que la API crezca).*

#### 🟢 [Nombre del Módulo / Recurso]
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET`  | `/api/v1/ejemplo` | Retorna una lista de ejemplos. |
| `POST` | `/api/v1/ejemplo` | Crea un nuevo registro. |

> **Nota para el desarrollador:** Documenta aquí cualquier lógica compleja, flujos de autenticación o reglas de negocio que no sean evidentes en la documentación autogenerada de Swagger.
