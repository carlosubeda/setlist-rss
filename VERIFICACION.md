# Verificación — 17 de noviembre de 2026

Se ejecutó el generador contra la página pública real, sin API ni autenticación.

- Recorrido completo de las tres páginas mediante sesión HTTP.
- Total anunciado por setlist.fm: 103 conciertos.
- Resultado: 103 entradas RSS y 103 identificadores únicos.
- XML analizado correctamente; todas las entradas tienen título, enlace, identificador y fecha.
- Flujo de GitHub Actions adaptado para instalar dependencias y generar el RSS sin secretos.

No se ha ejecutado el workflow en GitHub ni publicado una URL: no hay acceso a una cuenta o repositorio de GitHub en esta sesión. La prueba HTTP local no garantiza que setlist.fm acepte las peticiones desde los servidores de GitHub. El primer despliegue debe comprobarse allí.
