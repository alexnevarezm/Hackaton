# Ratio

Análisis estimado para juicios ordinarios laborales en la ciudad de Aguascalientes, México, comparado con datos públicos del tribunal.

Un abogado suele responder "¿qué posibilidades tengo de ganar?" con experiencia e intuición, porque nadie alcanza a leer todo lo que resuelve un tribunal. Ratio reúne esa información para respaldar esa respuesta.

**Ratio da un resultado probable, no real.** La estimación puede cambiar en cualquier momento según las circunstancias de cada juicio y su desarrollo probatorio, y no sustituye el criterio del abogado responsable.

## Estado
En desarrollo. El estimador aún no se ha probado con escritos reales de demanda y contestación.

## Fuentes
- Más de 6,800 juicios ordinarios y más de 63 mil acuerdos publicados desde julio de 2022.
- 761 sentencias públicas de juicios ordinarios.
- 1,549 criterios de la Suprema Corte, de alcance nacional.

## Validación
- Resultado y rebeldía: 39 de 40 aciertos cada uno en una muestra leída a mano.
- Estimador, con sentencias posteriores al 01/09/2025 (52 casos): AUC 0.765. Usa variables extraídas de la sentencia final, así que su desempeño real con escritos iniciales probablemente será menor.

## Contenido
- `scripts/`: descarga, extracción, análisis, estimador y bóveda de Obsidian.
- `sitio/`: página de Ratio y su video.
- `video/`: generador del video y narración.

Los datos no se incluyen, por lo que los scripts no corren sin ellos. Tampoco se publican la base de expedientes, las sentencias ni la bóveda.

## Hecho con Claude
Proyecto construido con Claude Code: programación, análisis, subagentes para la lectura de sentencias, video y sitio.
