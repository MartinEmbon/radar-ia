# Digital Worker: metodología de colaboración

Resumen de la metodología de trabajo con el Digital Worker (DW) de Digibee, tomado de la app de
práctica de Martín (github.com/MartinEmbon/digital-worker). Es la base de la sección
"Digital Worker". **No inventes comandos ni funciones del producto que no estén acá**: si una
táctica es tuya, marcala como propuesta.

## La idea central
El DW conduce una entrevista estructurada para subir la fidelidad del **SPEC**. La persona aporta
la **intención** y toma las decisiones; el DW analiza, propone y genera. El artefacto que queda
para el cliente no es el pipeline: es el SPEC, que es la fuente de verdad.

## La intención (el primer movimiento)
- Dice el resultado esperado y qué tiene que pasar para que cuente como éxito.
- No entrega la implementación: nada de conectores ni cantidad de pipelines al principio.
- Errores típicos: implementación disfrazada de intención, o un pedido tan vago que no sirve de
  punto de partida ("hay problemas con los pedidos").

## Fases y roles
1. **Entendimiento del negocio y del proceso**. El DW actúa como analista de negocio: reconstruye
   el proceso y los objetos de negocio. Vos aportás el paquete de contexto (specs de API, payloads
   de ejemplo, tablas de mapeo, reglas, excepciones conocidas) y la intención. Pedile que separe
   hechos confirmados, supuestos, preguntas abiertas y decisiones pendientes.
   Señal de error: ya estás nombrando conectores o pipelines.
2. **Mecánica de integración**. Analista técnico: origen, destino, dirección, disparador, unidad
   de procesamiento, frecuencia, latencia, volumen, orden y dependencias. Vos decidís qué se
   acepta como confirmado; pedile que diga de qué fuente sale cada respuesta.
3. **Arquitectura**. Propone topologías con sus trade-offs. Vos aprobás la topología: el límite
   entre pipelines decide qué se puede reprocesar solo. Comandos: `/propose-pipeline-topology`,
   `/design-path-variations`, `/design-each-pipeline`. Señal de error: reabre una topología
   aprobada sin un conflicto real, o presenta como confirmada una que nunca se aprobó.
4. **Especificación de implementación**. Contratos, mapeos, transformaciones, errores, reintentos,
   idempotencia, reprocesamiento, observabilidad, escenarios de prueba. Vos decidís el
   comportamiento ante errores; los valores por defecto de reintento y DLQ no son decisiones hasta
   que alguien los confirma. Comandos: `/define-data-mapping`, `/design-error-resilience`.
5. **Chequeo de preparación**. Revisor: PASS, FAIL o NEEDS CONFIRMATION, con criterio, evidencia
   y corrección exacta. Comando: `/review-spec-for-build`. Prueba: si le das el SPEC a un colega,
   ¿construye el mismo comportamiento?
6. **Generación y validación**. Genera pipelines candidatos, más casos de prueba, datos de prueba,
   mocks, diagramas y un backlog de aclaraciones. Vos revisás el flowSpec contra el SPEC y las
   buenas prácticas. Si algo diverge, se corrige el SPEC y se regenera; parchear el pipeline y
   dejar el SPEC viejo rompe la fuente de verdad.
7. **Conocimiento reutilizable**. Bibliotecario: decisiones, patrones, mapeos, riesgos y
   criterios para futuras integraciones. Comando: `/harvest-reuse`. Vos decidís qué entra a la
   memoria: promover un detalle del caso como si fuera un principio contamina las integraciones
   que vienen.

Escribiendo `/` en el chat del DW se ve la lista completa de comandos.

## Las ocho dimensiones del SPEC
Cada una puede estar subespecificada, en alta fidelidad o sobreespecificada. Alta fidelidad es
suficiente, no máxima.
1. Sistemas y autenticación. 2. Datos mapeados. 3. Caminos felices. 4. Variaciones de camino.
5. Errores y resiliencia. 6. Performance. 7. Seguridad. 8. Operación (qué se loguea, qué alerta
y a quién).
Ejemplo en errores: "manejar los errores adecuadamente" está subespecificado; "falla de
transporte: 3 intentos cada 5 segundos; rechazo de crédito: loguear y mandar a revisión manual;
respuesta vacía: fallar el registro y seguir la corrida" es alta fidelidad.

## Desambiguar un pedido
El DW no frena a preguntar cuál de las lecturas quisiste decir: elige una y sigue. Un pedido se
vuelve requisito cuando dice disparador, comportamiento y límite.
- **EARS** (comportamiento del pipeline): "Cuando <disparador>, el pipeline debe <respuesta>";
  "Mientras <estado>, ..."; "Si <condición>, entonces ...".
- **Gherkin** (un caso concreto): "Dado <contexto>, cuando <evento>, entonces <resultado>".
No hace falta escribir todo en EARS: se usa donde hay ambigüedad que cambia el comportamiento.

## Hechos y supuestos
Distinguir lo que está respaldado por una fuente de lo que todavía hay que confirmar. Un supuesto
presentado como hecho es el error más caro.

## La autopsia del mega-prompt
Un pedido de un párrafo que mezcla todo suele traer de más implementación y de menos intención:
invierte el orden de la metodología.

## Temario para rotar
Cuando el día no trae un disparador claro, la sección toma el siguiente tema de esta lista que no
tenga nota todavía (campo `tema_dw` en las notas de `Equipos/DW/`):
1. Escribir la intención
2. Armar el paquete de contexto
3. Separar hechos, supuestos, preguntas y decisiones
4. Fase 2: confirmar la mecánica de integración
5. Aprobar la topología (y cuándo frenar al DW)
6. Desambiguar con EARS
7. Fijar un caso con Gherkin
8. Errores y resiliencia: de "manejar errores" a modos de falla con nombre
9. Variaciones de camino
10. Datos mapeados y qué pasa cuando un campo no llega
11. Operación: qué se loguea y quién se entera
12. Sobreespecificar también es un error
13. El chequeo de preparación y la prueba del colega
14. Revisar el flowSpec: corregir el SPEC, no el pipeline
15. Cosechar conocimiento sin contaminar la memoria
16. Autopsia de un mega-prompt
