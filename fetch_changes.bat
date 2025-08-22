@echo off

REM Este script trae los últimos cambios del repositorio de GitHub

REM Cambiar al directorio del repositorio
cd /d C:\proyectos\video1\backend\video_backend

REM Obtener los últimos cambios de la rama actual
git pull origin HEAD

pause
