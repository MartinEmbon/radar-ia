# The AI SDLC transformation playbook (Atlassian, 2026)

Notas de lectura del PDF que compartió Martín (15 páginas, Atlassian, copyright 2026). Es un
resumen propio por secciones para la Práctica del día; no es el texto original. Lo que Atlassian
presenta como su producto (Teamwork Graph, Jira, Loom, DX) se cuenta como el enfoque de un
proveedor, no como una recomendación neutral. Los números son de benchmarks internos de
Atlassian, sin metodología publicada en el documento.

<a id="panorama"></a>
## 1. Panorama: los 7 pilares

- Tesis: el SDLC nativo de IA va mucho más allá de que los devs usen agentes de código. Como se
  escribe menos código a mano, programar pasa de una tarea sincrónica y de un solo hilo a una
  asincrónica y en paralelo. Eso deja al descubierto que los cuellos de botella están antes y
  después del código: planificación, diseño, revisión y mantenimiento. Y la colaboración del
  equipo se vuelve un cuello de botella todavía mayor cuando el trabajo se acelera.
- 7 pilares en dos grupos:
  - Inversiones de plataforma: contexto y medición.
  - Cambios de flujo de trabajo: planificación, diseño, desarrollo, revisión y mantenimiento.
- Los "sistemas de registro" (systems of record) unen todo: capturan la actividad y el
  conocimiento para que las personas apliquen criterio y los agentes tengan datos estructurados.
- Plataforma y flujos dependen uno del otro: los flujos nuevos solo funcionan con buen contexto y
  ciclos de feedback, y el contexto solo es confiable si los flujos nuevos registran su metadata.
  Las interacciones entre devs y agentes se vuelven, a su vez, contexto nuevo.
- Agile y DevOps acortaron los ciclos, pero no eliminaron las demoras de cada traspaso
  (hand-off). El SDLC nativo de IA colapsa esos traspasos en ciclos continuos donde producto,
  diseño e ingeniería crean juntos con apoyo de agentes.
- La mayoría de las organizaciones hoy está en algún punto entre el modelo tradicional y el
  nativo de IA.

<a id="contexto-y-medicion"></a>
## 2. Inversiones de plataforma: contexto y medición

**Contexto.**
- Por qué importa: los agentes tienen la inteligencia para escribir y revisar código, pero
  enfrentan el mismo problema que los equipos: entender el contexto de cada tarea (código,
  estrategia, decisiones de arquitectura, estándares, restricciones). Las personas lo acumulan
  durante años; los agentes lo necesitan en cada tarea.
- Cómo se ve bien: un grafo de contexto que conecta repositorios, tickets, documentación,
  estándares técnicos, grabaciones de reuniones y chat, accesible para personas y agentes con
  los mismos permisos. Así la IA actúa como un compañero informado en vez de adivinar la forma
  del sistema.
- Enfoque de Atlassian: Teamwork Graph, con más de 50 fuentes conectadas, accesible vía MCP o
  CLI. Lo que una persona puede ver es exactamente lo que un agente puede tocar. La actividad de
  personas y agentes vuelve al grafo, y el contexto se acumula con el uso.
- Dato interno de Atlassian: los agentes con acceso al grafo dieron resultados 44% más precisos
  usando 48% menos tokens.
- Cita de un CTO cliente (SpotOn), en esencia: cuando un agente arranca en el lugar equivocado,
  todo se vuelve más lento y caro, porque los devs terminan explicando dónde mirar y por qué el
  código es así.

**Medición.**
- Por qué importa: con tanto cambio, sin datos no se sabe qué funciona.
- Cómo se ve bien: la actividad del trabajo y de los agentes tiene que ser observable y medible;
  combinar datos cuantitativos (sistemas de registro, APIs, sesiones de agentes) con señales
  cualitativas de los devs.
- Enfoque de Atlassian: usan DX para combinar datos de Jira, Cursor y Claude Code con feedback
  cualitativo, y fijar metas e inversiones.

<a id="planificacion-y-diseno"></a>
## 3. Cambios de flujo: planificación y diseño

**Planificación.**
- Fricción: requisitos escritos a mano por gente que no conoce bien el código; las specs pierden
  restricciones de arquitectura y deuda técnica, y eso genera retrabajo caro en la implementación.
- Cambio: los agentes sintetizan las necesidades del cliente y el contexto de la organización en
  requisitos y specs. Las personas dejan de escribir specs desde cero y pasan a aplicar criterio:
  refinar, decidir y asegurar que el plan esté anclado en la realidad antes de construir.
- En la tabla comparativa: las specs quedan versionadas en el repositorio.

**Diseño.**
- Fricción: el diseño es una fase aislada; mockups estáticos y briefs que se pasan a ingeniería,
  y cualquier ajuste depende de un dev.
- Cambio: el diseño pasa a ser un hilo continuo integrado con planificación y desarrollo. Las
  sesiones de los agentes se guían por estándares guardados junto al código; prototipos vivos en
  lugar de pantallas estáticas.
- Enfoque de Atlassian: los estándares de diseño viven en el grafo, así los cambios respetan
  sistemas existentes, decisiones previas y dependencias entre equipos.

<a id="desarrollo-y-revision"></a>
## 4. Cambios de flujo: desarrollo y revisión

**Desarrollo.**
- Fricción: la calidad depende de la habilidad individual y la velocidad, del ritmo humano.
- Cambio: la calidad del código ya no depende del talento individual, sino de la calidad del
  contexto que recibe la IA. Y la velocidad depende de orquestar bien varios agentes junto a los
  ingenieros. Las tareas nacen de señales operativas y se registran automáticamente.
- Enfoque de Atlassian: las decisiones de cada sesión vuelven al grafo, así el conocimiento se
  acumula entre equipos en vez de quedar aislado en cada repositorio.
- Dato interno de Atlassian: el tiempo de ciclo de un issue bajó casi a la mitad, de 11,5 a 6,7
  días, por ciclos de feedback más cortos, revisiones más rápidas y agentes haciendo trabajo de
  rutina en paralelo.
- Cita de un SVP de ingeniería cliente (Outreach), en esencia: no se trata de escribir código más
  rápido sino de mejorar todo el ciclo.

**Revisión.**
- Fricción: los PRs esperan horas o días; cada revisor aplica estándares distintos; el código se
  valida en corrección, pero la intención y los requisitos recién se validan en staging o
  producción.
- Cambio: los agentes revisan primero, con estándares codificados en contexto compartido y
  aplicados a código nuevo y existente. La persona sigue tomando la decisión, pero llega mejor
  informada y con lo rutinario resuelto.
- Enfoque de Atlassian: trazabilidad completa del PR hasta la intención y los requisitos que lo
  originaron; estándares definidos centralmente y gobernanza auditable; detectar brechas entre lo
  que se pidió y lo que se construyó.

<a id="mantenimiento"></a>
## 5. Cambios de flujo: mantenimiento

- Fricción: mantenimiento reactivo y manual; triaje de errores a mano; el trabajo de
  confiabilidad (KTLO) se posterga frente a features, y se acumula deuda y riesgo.
- Cambio: modelo proactivo. Los agentes clasifican errores y generan el análisis de causa raíz
  antes de que intervenga una persona, y escalan solo cuando hace falta. El mantenimiento de
  rutina se delega a agentes autónomos.
- Enfoque de Atlassian: los agentes rastrean el impacto entre equipos y devuelven el trabajo
  relacionado a la planificación; ciclos de agentes "gobernados" que buscan trabajo bien definido
  en el backlog. Cada ciclo registra qué hizo y por qué: queda una auditoría viva.
- Dato interno de Atlassian: los ciclos de agentes en Jira resuelven automáticamente el 51% de las
  vulnerabilidades potenciales.

<a id="navegar-el-cambio"></a>
## 6. Navegar el cambio: las cinco jugadas

- Tesis: el SDLC nativo de IA es una transformación del modelo operativo: cambia cómo se define el
  alcance, cómo se logra la calidad, cómo se decide y cómo aprenden los equipos. Tratarlo como una
  compra (elegir agentes, licenciar modelos, cambiar de IDE) da, como mucho, mejoras
  incrementales.
- Las cinco jugadas que recomiendan a los líderes de ingeniería:
  1. **Anclarse en el contexto:** el contexto organizacional conectado y con permisos es la base;
     sin él, cualquier cambio de flujo rinde menos.
  2. **Medir temprano:** ciclos de feedback cuantitativos y cualitativos antes de escalar, para
     separar ganancias reales de hype.
  3. **Elegir un flujo para empezar:** la etapa del SDLC donde más valor se libere, y profundizar
     antes de ampliar.
  4. **Preservar la responsabilidad:** las personas a cargo del criterio, la calidad y la
     gobernanza; la IA ejecuta y hace cumplir. Los ciclos de agentes gobernados (acotados, que
     conocen los estándares y quedan registrados) son los que escalan.
  5. **Construir el modelo operativo, no solo la caja de herramientas:** actualizar rituales,
     roles y métricas de éxito junto con las herramientas.
