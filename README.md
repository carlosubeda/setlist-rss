# RSS diario de los conciertos de carlosubeda

Convierte los conciertos que `carlosubeda` marca como asistidos en setlist.fm en un RSS 2.0 público, actualizado **cada día** con GitHub Actions y GitHub Pages. Incluye todo el historial disponible en la API, con entradas ordenadas por fecha de concierto; la fecha de publicación de cada entrada corresponde a ese concierto, no al momento en que se marca la asistencia.

## Configuración (una sola vez)

1. Entra en https://api.setlist.fm/docs/1.0/ui/index.html y solicita una clave de API con tu cuenta de setlist.fm. Es gratuita para uso no comercial, sujeta a las condiciones de la plataforma.
2. Crea un repositorio **público** de GitHub llamado `setlist-rss` y sube los archivos de esta carpeta, **incluyendo** `.github/workflows/rss.yml`.
3. En GitHub, abre **Settings → Secrets and variables → Actions → New repository secret**. Nombre: `SETLIST_API_KEY`; valor: tu clave. No publiques la clave.
4. En **Settings → Pages → Build and deployment**, selecciona **Source: GitHub Actions**.
5. En **Actions → Actualizar RSS de conciertos → Run workflow** ejecuta la primera actualización. Revisa el estado de la ejecución.

La dirección de suscripción será:

`https://TU-USUARIO-DE-GITHUB.github.io/setlist-rss/rss.xml`

Puedes abrirla en cualquier lector RSS. El flujo programado se lanza diariamente a las **06:17 UTC** (07:17 en invierno / 08:17 en verano, hora de Madrid). GitHub puede retrasar o suspender las ejecuciones programadas en algunos supuestos; no es una garantía de ejecución al minuto.

## Notas

- Utiliza la **API oficial** `GET /1.0/user/carlosubeda/attended`, con paginación; no necesita extraer HTML.
- Si falla una actualización, GitHub Pages conservará la versión publicada anteriormente.
- No se guardan datos de los conciertos en el repositorio: cada publicación se genera de nuevo y se entrega como artefacto de Pages.
- RSS tradicional: algunos lectores muestran los conciertos antiguos como históricos, aunque se añadan hoy a setlist.fm. El canal incluye `lastBuildDate` actualizado diariamente y `guid` estable por concierto.
- Respeta las condiciones de uso y atribución de setlist.fm: https://www.setlist.fm/help/terms
