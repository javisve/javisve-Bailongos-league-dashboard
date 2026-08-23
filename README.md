# ⚽ Dashboard Comunitario de Biwenger

Un panel web moderno, interactivo y automático para compartir con tus amigos de la liga de Biwenger, **100% gratuito y sin dar ninguna ventaja competitiva**.

---

## ✨ Características y Secciones Incluidas

1. 🏆 **Clasificación General & Plantillas**:
   - Puntuaciones totales, valor actual de mercado de cada plantilla, número de jugadores y total de traspasos.
   - Al pulsar sobre cualquier mánager se despliega su plantilla interactiva (foto, club, posición, precio y puntos).
   - Buscador rápido para encontrar en qué equipo está cualquier jugador de la liga.
2. 🎖️ **Cuadro de Honor & Trofeos**:
   - 💥 **La Masterclass**: Mayor puntuación de la liga.
   - 🧱 **La Jornada Negra**: Puntuación más baja de la liga.
   - ⭐ **Capitán General**: El mánager con el jugador más determinante/goleador.
   - 🔄 **El Míster Rotaciones**: El mánager que más mueve su equipo.
   - 💎 **El Rey Midas**: Mánager con la plantilla más cara actualmente.
   - 🪙 **El Monje / Austero**: Mánager con el equipo de menor valor económico.
   - 🏷️ **El Chollo de la Liga**: Jugador con mejor ratio Puntos / Millón gastado.
   - 💸 **El Pozo sin Fondo**: Jugador más caro con peor rendimiento en puntos.
   - 🚜 **La Máquina de Fichar**: Mánager con más traspasos/ventas realizadas.
   - 🏟️ **El Monotemático**: Mánager con más futbolistas del mismo club de LaLiga.
3. ⚽ **El Once Ideal de la Liga**:
   - Campo de fútbol táctico interactivo con la mejor alineación posible combinando los mejores jugadores de todos los miembros.
4. 💎 **Curiosidades & Tops**:
   - 💰 Top 5 Jugadores Más Caros y sus dueños.
   - 🔥 Top 5 Jugadores con Más Puntos y sus dueños.
   - 🧤 **El Muro**: Top mejores porteros y defensas.
   - 👟 **La Bota de Oro**: Top delanteros de la comunidad.
   - 🃏 **Los Reyes del Negativo**: Jugadores con puntuaciones negativas o restas de puntos.

---

## 🔒 Política de Fair Play (Juego Limpio)

* ❌ **Cero ventajas**: No se muestra el dinero en cuenta de ningún rival ni pujas activas.
* ✅ **100% Transparente**: Solo se analizan datos públicos oficiales de Biwenger.

---

## 🚀 Cómo publicar gratis en GitHub Pages (en 2 minutos)

1. **Sube tu repositorio a GitHub** (puede ser privado o público).
2. **Añade tus credenciales en GitHub Secrets**:
   - Ve a tu repositorio en GitHub > `Settings` > `Secrets and variables` > `Actions`.
   - Crea 2 nuevos secretos:
     - `BIWENGER_EMAIL`: Tu correo de Biwenger.
     - `BIWENGER_PASSWORD`: Tu contraseña de Biwenger.
3. **Activa GitHub Pages**:
   - Ve a `Settings` > `Pages`.
   - En **Source**, selecciona **GitHub Actions**.
4. **¡Listo!**:
   - El workflow en `.github/workflows/deploy_dashboard.yml` se ejecutará automáticamente todos los días (a las 07:00 y 23:00 UTC) y publicará tu web en la URL gratuita `https://<tu-usuario>.github.io/<tu-repo>/`.
   - Puedes forzar una actualización cuando quieras desde la pestaña `Actions` > `Actualizar y Desplegar Dashboard Biwenger` > `Run workflow`.

---

## 💻 Uso Local

Para probarlo en tu ordenador:
```bash
# 1. Extraer los datos actuales de Biwenger
python dashboard_comunidad/update_data.py

# 2. Abrir la web en tu navegador
# Simplemente haz doble clic en dashboard_comunidad/index.html
```
