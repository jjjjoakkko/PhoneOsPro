Herramienta OSINT para Teléfonos
Una herramienta profesional y ética para Inteligencia de Fuentes Abiertas (OSINT) en números telefónicos. Este es un script único en Python que analiza números de teléfono utilizando estándares públicos, proporcionando información como país, región, operador, tipo de línea, zonas horarias y varios formatos.
Nota Importante: Esta herramienta es solo para fines educativos y éticos. No accede a bases de datos privadas, no realiza búsquedas en tiempo real ni garantiza precisión actual. Todos los datos se derivan de estándares públicos de números telefónicos (por ejemplo, E.164). No la utilice para actividades ilegales, acoso o invasión de la privacidad.
Características

Valida y normaliza números telefónicos.
Proporciona información sobre país, región, operador y tipo de línea con niveles de confianza.
Muestra zonas horarias asociadas al número.
Salidas en múltiples formatos (E.164, internacional, nacional).
Salida en consola con colores para mayor legibilidad.
Exportaciones opcionales a JSON o CSV.
Registra consultas para auditoría (en phone_osint.log).

Requisitos

Python 3.6 o superior.
Bibliotecas externas (instale mediante requirements.txt):
phonenumbers
colorama
tabulate


Instalación

Clone el repositorio:textgit clone https://github.com/tuusuario/herramienta-osint-telefonos.git
cd herramienta-osint-telefonos
Instale las dependencias:textpip install -r requirements.txt
Haga el script ejecutable (opcional):textchmod +x phone_osint.py

Uso
Ejecute el script con un número de teléfono en formato internacional (se recomienda E.164, por ejemplo, +5491155667788).
textpython phone_osint.py <número> [--json] [--csv]

<número>: El número de teléfono a analizar.
--json: Exporta los resultados a phone_osint_output.json.
--csv: Exporta los resultados a phone_osint_output.csv.

Ejemplos
Análisis básico:
textpython phone_osint.py +15551234567
Con exportación a JSON:
textpython phone_osint.py +15551234567 --json
Ejemplo de Salida
textPhone OSINT Tool — Ethical & Professional

── INPUT ──────────────────────────────
📥 Original     : +15551234567
🧼 Normalizado  : +15551234567
✔ Válido       : True

── ANÁLISIS ──────────────────────────────
🌍 País        : United States [HIGH]
📍 Región      : United States [MEDIUM]
📡 Operador    : Verizon [MEDIUM]
📶 Tipo línea  : MOBILE [MEDIUM]
🕒 Zona horaria: America/New_York, America/Chicago [MEDIUM]

── FORMATOS ──────────────────────────────
📞 E.164        : +15551234567
🌐 Internacional: +1 555-123-4567
🏠 Nacional     : (555) 123-4567

── NOTAS ──────────────────────────────
⚠️ La información mostrada se basa en estándares públicos.
⚠️ No indica ubicación exacta ni operador actual garantizado.
Limitaciones

La información de operador y región puede no reflejar números portados o cambios recientes.
Sin acceso a datos en tiempo real o privados: se basa en la biblioteca phonenumbers.
Los niveles de confianza son basados en heurísticas.

Contribuciones
Siéntase libre de hacer un fork y enviar pull requests. Asegúrese de que todos los cambios mantengan estándares éticos.