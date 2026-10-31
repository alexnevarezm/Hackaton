# Ratio

Aplicación para estimar escenarios en juicios ordinarios laborales de la ciudad de Aguascalientes, México, comparando un asunto con datos públicos del tribunal.

**Ratio da un resultado probable, no real.** Puede cambiar según las circunstancias de cada juicio y su desarrollo probatorio, y no sustituye el criterio del abogado responsable.

## Cómo usarla
1. Descarga [`app/index.html`](app/index.html) con el botón de descarga de GitHub.
2. Ábrela en tu navegador. No requiere instalación ni internet.
3. Indica si habrá contestación válida, la acción y las defensas.

Verás la estimación con su rango, alertas de contradicciones, qué preparar y cómo le ha ido a cada defensa. Lo que captures no sale de tu navegador.

## Estado
Prototipo. No se ha probado con demandas y contestaciones reales.

## Datos
- Más de 6,800 juicios ordinarios y más de 63 mil acuerdos publicados desde julio de 2022.
- 760 sentencias públicas de juicios ordinarios.
- 1,549 criterios de la Suprema Corte, de alcance nacional.

La aplicación solo contiene coeficientes y cifras agregadas: no incluye partes, juzgadores, sentencias ni fichas.

## Validación
- Modelo con 248 sentencias contestadas: AUC de 0.711 en validación cruzada y 0.756 con 52 sentencias desde el 01/09/2025.
- Las defensas se tomaron de la sentencia final, así que el desempeño con solo escritos iniciales puede ser menor.
- Lectura de sentencias automatizada, no revisada una por una.

## Contenido
- `app/`: la aplicación.
- `scripts/`: descarga, extracción, análisis y modelo. No corren sin los datos, que no se publican.

## Hecho con Claude
Construido con Claude Code: programación, análisis y subagentes para leer sentencias.
