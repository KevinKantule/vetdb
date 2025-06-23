Sistema de Gestión Veterinaria (VetDB)

Este proyecto es un sistema CRUD para la gestión de una veterinaria, implementado con Snowflake (Back‑end) y Streamlit + Python (Front‑end). Incluye autenticación, CRUD para Dueños, Mascotas y Citas, auditoría, soft‑delete, y reportes.


📂 Estructura de carpetas
app/
├── auth.py             # Login y control de sesión
├── common.py           # Conexión y run_query singleton
├── crud/
│   ├── duenos.py       # CRUD Dueños
│   ├── mascotas.py     # CRUD Mascotas
│   ├── citas.py        # CRUD Citas
│   └── reportes.py     # Funciones de reportes
├── logging_config.py   # Configuración de logger
└── main.py             # Streamlit UI principal

secrets.toml            # Credenciales de Snowflake
README.md               # Documentación (este archivo)
reset_and_seed.sql      # Script para limpiar y poblar datos de prueba


⚙️ Tecnologías y herramientas
- Python 3.12+
- Streamlit para UI
- Snowflake Connector para Python
- Snowflake (DB) 
- cryptography para key‑pair auth
- pandas para DataFrames en UI


🚀 Configuración y arranque
1. Clona el repositorio
git clone  && cd vetdb

2. **Crea y activa un entorno virtual**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

3. Define los secretos en secrets.toml:
[snowflake]
user="..."
account="..."
warehouse="WH_XS"
database="VETDB"
schema="PUBLIC"
role="ADMIN_ROLE"
private_key_path="/ruta/a/rsa_key.p8" o password="..."

4. **Pobla la base de datos** (opcional datos de prueba):
   ```bash
snowsql -f reset_and_seed.sql

5. Inicia la app:
streamlit run app/main.py


## 🔍 Checklist de buenas prácticas

- ✅ Consultas parametrizadas (`%s`)
- ✅ Autenticación por key‑pair o password vía `st.secrets`
- ✅ Manejo de errores con `try/except` y `logger`
- ✅ Transacciones con `commit()/rollback()`
- ✅ Singleton de conexión con `@st.cache_resource`
- ❌ Pool de conexiones (opcional)
- ✅ Paginación y filtros dinámicos en UI
- ✅ UI modular por entidades (Dueños, Mascotas, Citas)
- ✅ Docstrings y logging en backend

## 🛠 Próximos pasos / mejoras

1. Añadir un pool de conexiones si se requiere alta concurrencia.
2. Elaborar reportes avanzados con lenguaje natural y descargas Excel.
3. CI/CD y despliegue automático en Streamlit Cloud.
4. Traducción y temas de UI, notificaciones (email/SMS).

---


**¡Gracias por usar VetDB!**