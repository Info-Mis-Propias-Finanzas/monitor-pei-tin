# Monitor PEI y TIN (Real Estate by MPF)

Página estática que muestra el precio de cierre de PEI y TIN en la Bolsa de Valores de Colombia, el descuento frente a su valor patrimonial, distribuciones, portafolio, deuda, histórico, una calculadora aritmética y el calendario de reportes. Tiene dos vistas: la general y la avanzada para analistas, que se activa con el interruptor de la barra superior.

No necesita servidor de aplicaciones ni base de datos. Es HTML, CSS y JavaScript que leen archivos JSON de la carpeta `data/`.

## Contenido

| Ruta | Qué es |
|---|---|
| `index.html` | La página completa (estilos, marcado y lógica). |
| `assets/brand.css` | Tipografía Plus Jakarta Sans embebida. |
| `assets/d3.min.js` | D3 v7.9.0, usado para las gráficas. |
| `assets/dash-shim.js` | Capa que carga los JSON de `data/` y los entrega a la página. |
| `data/*.json` | Los ocho conjuntos de datos (ver abajo). |
| `scripts/actualizar_precios.py` | Agrega a `data/precios.json` los cierres nuevos de la BVC. |
| `.github/workflows/actualizar-precios.yml` | Ejemplo de tarea diaria en GitHub Actions. |

## Probarla en local

Los navegadores no dejan leer JSON abriendo el archivo con doble clic, así que hay que servir la carpeta:

```
cd monitor-pei-tin
python3 -m http.server 8000
```

y abrir http://localhost:8000.

## Publicarla

Sirve en cualquier hosting estático (Netlify, Vercel, Cloudflare Pages, GitHub Pages, S3, o la carpeta pública del sitio actual). Se sube la carpeta completa tal cual.

Si los datos van a vivir en otra ruta (un bucket o un endpoint propio), basta con definir la ruta antes de cargar `assets/dash-shim.js` en `index.html`:

```html
<script>window.DASH_DATA_URL = 'https://ejemplo.com/monitor/data/';</script>
```

## Actualización diaria del precio

`scripts/actualizar_precios.py` consulta la API pública de históricos de la BVC (la misma que usa bvc.com.co), agrega los días que falten de PEI y TIN y reescribe `data/precios.json`. Solo usa la librería estándar de Python 3.9 o superior.

```
python3 scripts/actualizar_precios.py
```

Detalles para quien lo programe:

* Correrlo de lunes a viernes en la mañana, hora Colombia. Ignora el día en curso porque el cierre todavía no es definitivo, así que el dato más reciente siempre es el del día hábil anterior.
* Si la BVC no responde después de tres intentos, termina con código 1 y no toca el archivo. La página sigue mostrando el último cierre disponible con su fecha.
* La consulta necesita salida a `www.bvc.com.co` y `rest.bvc.com.co`. Si el servidor tiene firewall, hay que permitir esos dos dominios. Conviene probar una vez desde el servidor o desde GitHub Actions, porque algunos sitios bloquean IP de centros de datos.
* Opciones: cron en el servidor donde vive la página, la tarea de ejemplo de GitHub Actions (hace commit y el hosting vuelve a publicar) o una función programada del hosting.
* La página pide los JSON con `cache: 'no-cache'`; si hay CDN, conviene un TTL corto (una hora o menos) para `data/`.

## Datos que NO se actualizan solos

Estos archivos se actualizan a mano cuando PEI o TIN publican resultados (trimestral) o eventos relevantes. La página los lee tal cual; basta con editar el JSON respetando los mismos campos.

| Archivo | Contenido | Cuándo actualizar |
|---|---|---|
| `indicadores.json` | Una fila por fondo y trimestre: valor patrimonial por título, títulos, activos, deuda, LTV, costo de la deuda, vacancia, NOI, distribuciones, inversionistas, plazo de contratos. | Cada informe trimestral, y en TIN cuando paga distribuciones. |
| `reportes.json` | Informes publicados y próximos eventos con fecha y enlace. | Cuando se publica un informe o se anuncia una fecha. |
| `eventos.json` | Hechos que movieron el precio (emisiones, ventas, splits). | Cuando ocurra un evento relevante. |
| `finanzas.json` | Ingresos, NOI, EBITDA y gasto financiero por periodo. | Cada informe trimestral o anual. |
| `deuda.json` | Indexación de la deuda (IBR, IPC, tasa fija), bonos y créditos. | Cada informe trimestral. |
| `composicion.json` | Tipos de activo, ciudades, arrendatarios, sectores, vencimientos y el párrafo de perfil de cada fondo. | Una o dos veces al año. |
| `activos.json` | Inmuebles uno a uno con su valor. | Cuando salgan nuevos avalúos (informe anual). |

`precios.json` se mantiene con el script. Cada fila tiene `fondo`, `fecha`, `cierre`, `maximo`, `minimo`, `cantidad`, `volumen_cop`, `negociacion_continua` y `fuente`. Para TIN, `negociacion_continua` es falso antes del 21 de enero de 2026 porque hasta esa fecha su precio era de referencia y no se usa en los cálculos.

Las fechas van en formato `AAAA-MM-DD` y los trimestres siguen el formato de las filas existentes (por ejemplo `3Q2026`). Los montos van en pesos colombianos sin separadores.

## Avisos

La página incluye avisos de que es información educativa y no una recomendación de inversión: debajo de la portada, en la calculadora, en la nota de rentabilidad total del histórico y en el pie de página. No se deben quitar al integrar el formulario de captura de leads. En `index.html` hay un comentario que marca dónde va ese formulario, antes del pie de página.
