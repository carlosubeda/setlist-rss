# RSS diario de carlosubeda mediante scraping

Lee el HTML público de https://www.setlist.fm/attended/carlosubeda y recorre su paginación conservando la sesión web. Genera RSS 2.0 con todo el historial de conciertos. No utiliza la API ni necesita claves, contraseñas o secretos.

## Publicar en GitHub Pages

1. Crea un repositorio público llamado `setlist-rss`, con rama principal `main`.
2. Sube el contenido de esta carpeta a la raíz, incluyendo `.github/workflows/rss.yml`. No subas la carpeta contenedora como un nivel adicional. Para incluir `.github`, puedes usar Git o arrastrar la carpeta desde un explorador que muestre archivos ocultos.
3. En **Settings → Pages → Build and deployment → Source**, selecciona **GitHub Actions**.
4. En **Actions → Actualizar RSS de conciertos → Run workflow**, inicia la primera ejecución. Si GitHub solicita habilitar Actions, habilítalo.
5. Cuando termine correctamente, abre la dirección mostrada en el despliegue de Pages y añade `rss.xml` al final. Esa es la URL que debes pegar en tu lector RSS.

Ejemplo: `https://TU-USUARIO.github.io/setlist-rss/rss.xml`.

El workflow se ejecuta cada día a las 06:17 UTC: 07:17 en invierno y 08:17 en verano en Madrid. También permite ejecución manual y se inicia al subir cambios a `main`. GitHub puede retrasar las ejecuciones y desactivar la programación de repositorios públicos sin actividad durante 60 días; revisa Actions si deja de actualizarse.

## Ejecutar localmente

Requiere Python 3.12 o posterior:

```sh
python3 -m pip install -r requirements.txt
FEED_BASE_URL=https://TU-USUARIO.github.io/setlist-rss python3 build_feed.py
```

El resultado se guarda en `public/rss.xml`. `FEED_BASE_URL` indica la URL pública futura; este comando por sí solo no publica el archivo.

## Comportamiento

- Consulta las páginas del listado, con dos segundos entre páginas; no visita individualmente los conciertos.
- Verifica que la cantidad de conciertos únicos coincide con el total anunciado por la página.
- Si hay bloqueo, cambio de HTML, paginación repetida o extracción incompleta, falla sin desplegar un RSS vacío o parcial. Pages conserva el último despliegue correcto.
- Cada concierto tiene como identificador estable su URL. Las entradas se ordenan por fecha del concierto y usan esa fecha como `pubDate`, no la fecha en que se añadió a la lista. Algunos lectores tratarán como históricos los conciertos antiguos añadidos recientemente.
- Si eliminas una asistencia, desaparecerá del RSS en la siguiente ejecución correcta, aunque tu lector puede conservarla.
- Un cambio en el HTML de setlist.fm puede requerir adaptar el scraper. No se evaden CAPTCHA ni bloqueos.
- Fuente y atribución: setlist.fm. Condiciones: https://www.setlist.fm/help/terms

## Comprobación de esta entrega

Consulta `VERIFICACION.md` para el resultado de la ejecución real. El ZIP contiene el generador y la configuración; no constituye un feed alojado. El RSS solo se actualizará automáticamente cuando el workflow esté instalado y activo en GitHub.
