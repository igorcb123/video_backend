@echo off

REM Este script sube los cambios al repositorio de GitHub

REM Cambiar al directorio del repositorio
cd /d C:\proyectos\video1\backend\video_backend

REM Agregar todos los cambios al área de preparación
git add .

REM Solicitar un mensaje de commit al usuario
set /p commitMessage="Introduce el mensaje del commit: "

REM Crear el commit con el mensaje proporcionado
git commit -m "%commitMessage%"

REM Subir los cambios a la rama actual
git push origin HEAD

pause
