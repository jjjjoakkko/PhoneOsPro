# 📱 Phone OSINT Pro

Herramienta OSINT profesional para análisis de números telefónicos usando estándares públicos.

> ⚠️ **Uso ético:** Solo con fines educativos. Sin acceso a datos privados ni garantía de precisión actual.

## ✨ Características

- ✅ Valida y normaliza números (E.164)
- 🌍 País, región, operador y tipo de línea
- 🕒 Zonas horarias asociadas
- 📊 Exportación a JSON/CSV
- 🎨 Salida coloreada en consola

## 📋 Requisitos

- Python 3.6+
- Dependencias: `phonenumbers`, `colorama`, `tabulate`


## 🚀 Instalación

```bash
# Clonar repositorio
git clone https://github.com/jjjjoakkko/PhoneOsPro.git
cd PhoneOsPro

# Crear entorno virtual
python3 -m venv virtual

# Activar entorno
# Windows (PowerShell):
.\virtual\Scripts\Activate.ps1
# Windows (CMD):
.\virtual\Scripts\activate.bat
# Linux/Mac:
source virtual/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 💻 Uso

```bash
# Análisis básico
python PhoneOs.py +5491155667788

# Con exportación JSON
python PhoneOs.py +5491155667788 --json

# Con exportación CSV
python PhoneOs.py +5491155667788 --csv

# Ver ayuda
python PhoneOs.py -h
```

**O usa el lanzador para Windows:**
```powershell
.\run.bat +5491155667788
```

## 📤 Formatos de Salida

| Formato | Ejemplo |
|---------|---------|
| E.164 | `+5491155667788` |
| Internacional | `+54 9 11 5566-7788` |
| Nacional | `011 5566-7788` |

## 🔍 Ejemplo de Salida

```
── INPUT ──────────────────────────────
📥 Original     : +15551234567
🧼 Normalizado  : +15551234567
✔ Válido       : True

── ANÁLISIS ──────────────────────────────
🌍 País        : United States [HIGH]
📡 Operador    : Verizon [MEDIUM]
🕒 Zona horaria: America/New_York [MEDIUM]

── FORMATOS ──────────────────────────────
📞 E.164        : +15551234567
🌐 Internacional: +1 555-123-4567
🏠 Nacional     : (555) 123-4567
```

## ⚙️ Limitaciones

- No accede a datos en tiempo real ni privados
- La info de operador puede no reflejar portabilidad
- Basado en la librería `phonenumbers`
- Niveles de confianza heurísticos

## 🤝 Contribuciones

Forks y PRs bienvenidos. Mantén estándares éticos.