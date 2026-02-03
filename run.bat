@echo off
REM Activar virtualenv local y ejecutar PhoneOs.py con los argumentos pasados.
SET SCRIPT_DIR=%~dp0
IF EXIST "%SCRIPT_DIR%virtual\Scripts\activate.bat" (
    CALL "%SCRIPT_DIR%virtual\Scripts\activate.bat"
    python "%SCRIPT_DIR%PhoneOs.py" %*
) ELSE (
    ECHO No se encontró el virtualenv en "%SCRIPT_DIR%virtual\Scripts\activate.bat"
    ECHO Ejecutando con el python del virtualenv si existe...
    "%SCRIPT_DIR%virtual\Scripts\python.exe" "%SCRIPT_DIR%PhoneOs.py" %*
)
