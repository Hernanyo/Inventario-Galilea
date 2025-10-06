* \# Instalación
* 
* \## Requisitos
* \- Python 3.11+ (recomendado)
* \- PostgreSQL 13+ (desarrollo/producción)
* \- Git (opcional, recomendado)
* 
* \## Pasos (Windows / PowerShell)
* ```bash
* \# 1) Clonar y entrar
* git clone https://github.com/Hernanyo/Inventario-Galilea.git
* cd Inventario-Galilea/inventario\_django
* 
* \# 2) Entorno virtual
* python -m venv .venv
* .\\.venv\\Scripts\\Activate.ps1
* 
* \# 3) Dependencias
* pip install -r requirements.txt
* 
* \# 4) Variables de entorno (.env)
* \# ver: Guía Rápida → Configuración
* 
* \# 5) Migraciones
* python manage.py migrate
* 
* \# 6) Superusuario
* python manage.py createsuperuser
* 
* \# 7) Arrancar
* python manage.py runserver
* 
