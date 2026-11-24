# BRIEF: Andén 9 (nombre de trabajo)

> Documento de arranque para los agentes. Contiene el objetivo, las decisiones tomadas, la arquitectura, el modelo de datos, las reglas de medición, el plan por hitos y la metodología (ODD, RDD y flujo Git) integrada en cada parte. Las reglas operativas permanentes viven en `AGENTS.md`; este brief describe **qué construir y en qué orden**.
> Idioma: este brief está en español. Código, commits, PRs e issues van en inglés. Los textos de la web van en español y sin guiones largos.
> Diseño de referencia: canvas "Nueves: status page de las APIs de Renfe" en claude.ai (https://claude.ai/artifact/CAoARe9RL1SnyxvmUP8US4), con cuatro artboards: Inicio (escritorio), Detalle de servicio, Metodología e Inicio (móvil). Los números del diseño son **datos de ejemplo**.

---

## 1. Objetivo

Una status page pública y **no oficial** que mide el uptime de las APIs de Renfe con los estándares de un SaaS y lo expresa en **número de nueves** (99,9 % = 3 nueves). Nace de un tweet que proponía construirla encima de Renfe CLI: se miden exactamente los servicios que usa `renfe-cli` de Luis González (MIT).

Qué cuenta como éxito en v1: una web desplegada que, con datos reales de al menos 7 días, muestra para cada servicio su estado actual, uptime y nueves en 24 h, 7, 30 y 90 días, latencia p50 y p95, una tira diaria de 90 días e incidentes, y que lo hace **con una metodología publicada y defendible** (sin falsos positivos por bloqueos ni por fallos propios).

## 2. Alcance

**Dentro de v1**
- Sonda (prober) que comprueba 8 endpoints de Renfe y un endpoint de control, con frecuencias educadas y user agent propio.
- Clasificación de cada comprobación en cinco estados: operativo, degradado, caído, bloqueado y sin datos.
- Persistencia en Postgres (Supabase), vistas agregadas con uptime, nueves, latencias y rollups diarios.
- Máquina de estados de incidentes (abrir tras 2 fallos seguidos, cerrar tras 2 éxitos seguidos).
- Web estática con las cuatro pantallas del diseño, responsive.
- Heartbeat de la propia sonda: si deja de medir, la web lo dice ("sin datos") en vez de inventar uptime.

**Fuera de v1** (no construir sin autorización explícita)
- Puntualidad de los trenes o cualquier métrica que no sea la disponibilidad de las APIs (se descartó a propósito: el proyecto se ciñe al tweet).
- Notificaciones (correo, Telegram, RSS), suscripciones, cuentas de usuario.
- Sondas desde varias regiones.
- Cercanías, Rodalies u otros operadores.
- Cualquier técnica para evitar bloqueos: rotación de IPs, proxies residenciales, navegadores headless, falsificar user agents, resolver captchas o colas.
- Comprar, reservar o iniciar pagos, aunque sea en modo invitado.

## 3. Decisiones ya tomadas

| Tema | Decisión |
|---|---|
| Qué se mide | Los servicios de Renfe que usa `renfe-cli` (observados por su autor el 15 a 22 nov 2026). Ver sección 6 |
| Sonda | Python 3.14, `httpx` asíncrono, `uv`; mismo ecosistema que `renfe-cli`, lo que facilita leer su código como referencia |
| Base de datos | Supabase (Postgres) con migraciones versionadas en `supabase/migrations/` y RLS |
| Web | React 19 + TypeScript (TSX) + Vite + Tailwind CSS + pnpm; TanStack Query para datos; sin backend propio, lee vistas públicas de Supabase con la clave anónima |
| Pruebas | Sonda: pytest + respx (HTTP grabado) + hypothesis para la matemática. Web: Vitest + Playwright (e2e y axe para accesibilidad) |
| Calidad estática | Sonda: ruff, mypy `--strict`, import-linter. Web: `tsc`, ESLint, dependency-cruiser |
| Hosting | Sonda en un VPS pequeño en España o en la UE (Docker + systemd). Web en Netlify. **Región y proveedor por confirmar** (incertidumbre 1) |
| Identidad de la sonda | User agent `anden9-probe/<versión> (+<url>/metodologia)`. Igual que `renfe-cli`, se presenta como lo que es, para que Renfe pueda identificarla y bloquearla si quiere |
| Diseño | Paleta propia (no la de Renfe), Space Grotesk, Inter y JetBrains Mono. Aviso "No oficial · sin relación con Renfe" en todas las páginas |
| Git | `main` <- `dev` <- ramas `feat/*`, `fix/*`, `chore/*`; los agentes hacen commit, push y abren PR hacia `dev`; **Albert hace todos los merges a mano** |

## 4. Arquitectura

```
                 cada 1 a 15 min (por sonda)
[scheduler] ──> [probes/<id>] ──HTTP──> servicios de Renfe
     │               │
     │               └──> [control] (solo si falla una sonda, y cada 5 min)
     │
     ▼
[classifier]  resultado HTTP ──> Outcome(up | degraded | down | blocked | unknown, reason)
     │
     ▼
[incidents]   máquina de estados por sonda (2 fallos abren, 2 éxitos cierran)
     │
     ▼
[writer] ──> Supabase Postgres: checks, incidents, heartbeat
                          │
                          ▼
              vistas públicas (uptime, nueves, diarios, latencia)
                          │  clave anónima, solo lectura (RLS)
                          ▼
                 [web] React 19 en Netlify
```

Principios:
- El **dominio** de la sonda (`classifier`, `incidents`, `uptime`) es puro: sin `httpx`, sin Supabase, sin reloj real. Define los puertos `HttpPort`, `Store` y `Clock`.
- Cada sonda es un módulo en `prober/src/anden9/probes/<id>.py` que implementa el protocolo `Probe` y se registra en un catálogo único (`catalog.py`). Para añadir una sonda se copia `probes/_template.py`.
- **La fórmula del uptime y de los nueves vive en un solo sitio:** las vistas SQL. La web solo da formato. Un fichero de casos compartido (`contracts/uptime_cases.json`) se ejecuta contra las vistas y contra el formateador de la web.
- La web no tiene backend: lee vistas, nunca tablas.

Estructura de directorios objetivo:

```
prober/
  pyproject.toml
  src/anden9/
    domain/          (classifier, incidents, outcome, ports; puro)
    probes/          (_template.py, catalog.py, una sonda por fichero)
    adapters/        (http_httpx.py, store_supabase.py, clock.py)
    scheduler.py
    cli.py           (anden9 probe once, anden9 run)
    config.py        (único sitio que lee el entorno; pydantic-settings)
  tests/             (unit, contract, fixtures/http grabadas)
web/
  src/
    features/        (status-overview, service-detail, methodology, incidents)
    data/            (cliente Supabase y queries; único acceso a datos)
    ui/              (componentes compartidos: barras de 90 días, badges, tabs)
    lib/format.ts    (formato de %, duraciones y nueves; sin cálculo)
  e2e/               (Playwright)
supabase/
  migrations/
  seed/              (datos de ejemplo para desarrollo y e2e)
contracts/           (uptime_cases.json)
docs/                (feature-map.md, runbook.md, glossary.md, probes.md)
odd/                 (documentos de feature que genera ODD)
scripts/             (repo-hygiene, request-budget)
```

## 5. Reglas de medición (el corazón del proyecto)

Si la web publica una caída que no existió, el proyecto pierde toda credibilidad. Por eso estas reglas son contrato y tienen tests.

### 5.1 Estados

| Estado | Cuándo | ¿Cuenta para el uptime? |
|---|---|---|
| `up` (operativo) | Código esperado, forma de datos válida y latencia por debajo del umbral de degradado | Sí, como disponible |
| `degraded` (degradado) | Válido pero lento, o datos vacíos o viejos cuando no deberían | Sí, como disponible (se muestra) |
| `down` (caído) | Timeout, conexión rechazada, error DNS o TLS, 5xx, o respuesta con forma inválida (incluido un 200 con HTML de error) | Sí, en contra |
| `blocked` (bloqueado) | 403, 429, página HTML de protección o sala de espera | **No**: se excluye del denominador |
| `unknown` (sin datos) | Falla la propia sonda, o el endpoint de control tampoco responde, o no hay comprobación en el intervalo | **No**: se excluye del denominador |

Cada resultado lleva un `reason` estable (`timeout`, `conn_refused`, `dns`, `tls`, `http_5xx`, `bad_shape`, `slow`, `empty`, `http_403`, `http_429`, `bot_page`, `control_failed`, `probe_error`, `gap`).

### 5.2 Fórmulas

- Cada comprobación cubre el intervalo desde su inicio hasta la siguiente, con un máximo de 2 veces su intervalo nominal. Lo que quede sin cubrir es `unknown` con reason `gap`.
- `uptime = (s_up + s_degraded) / (s_total - s_blocked - s_unknown)`, en segundos enteros.
- `nueves = floor(-log10(1 - uptime))`. Si no hubo ningún segundo caído, no hay nueves que calcular: se muestra "sin caídas" (nunca "infinitos nueves").
- Si el denominador es menor que el 50 % de la ventana, la ventana se marca como "datos insuficientes" y no se muestran nueves.
- Los porcentajes se **truncan** (no se redondean) a dos decimales, para que 99,996 % se vea como 99,99 % y no como 100,00 %.
- El uptime agregado de "Renfe" es la media de los servicios activos, con el mismo peso cada uno.

### 5.3 Incidentes

- Se abren tras **2 comprobaciones `down` seguidas** de la misma sonda (o 2 `degraded`, o 2 `blocked`, cada tipo por separado) y se cierran tras **2 `up` seguidas**. La duración cuenta desde el primer fallo.
- Un `down` solo es válido si el endpoint de control respondió bien en el mismo minuto. Si el control también falla, el resultado pasa a `unknown` con reason `control_failed`. Endpoint de control por defecto: `https://www.google.com/generate_204` (incertidumbre 9).

### 5.4 Juego limpio con Renfe (restricciones de comportamiento)

- Ninguna sonda se ejecuta más de una vez por minuto; las pesadas (búsqueda, venta clásica, catálogo, GTFS) como mucho cada 15 minutos.
- Una sola petición en vuelo por host. Sin reintentos dentro de una comprobación: la confirmación la dan los 2 fallos seguidos.
- Con un 429 y cabecera `Retry-After`, la sonda se pausa ese tiempo (máximo 1 hora) y el hueco se marca como `blocked`.
- Presupuesto total: **menos de 150 peticiones por hora** a Renfe, sumando todas las sondas. Un script de CI lo calcula a partir del catálogo y falla si se supera.
- La clave pública y el token de Renfe viven solo en memoria. Nunca se registran en logs ni se guardan.

## 6. Catálogo de sondas inicial

Fuente: `src/renfe/config.py`, `client.py`, `legacy.py` y `delays.py` de `renfe-cli`. Los agentes deben releer esos ficheros antes de implementar cada sonda, porque Renfe cambia cosas y su autor anota lo que observa.

| id | Servicio | Petición | Cada | Timeout | Degradado si | Válido si |
|---|---|---|---|---|---|---|
| `nsv-config` | Configuración web (venta nueva) | GET `https://venta.rsv.renfe.com/config/arch-config.json` | 5 min | 10 s | > 3 s | 200 y JSON con `arch.security.apiKey` string |
| `nsv-token` | Token público | GET `https://api.rsv.renfe.com/user/external-users-login/v1/tokens/public` con `x-api-key` (de `nsv-config`) y `channel: VLP` | 5 min | 10 s | > 3 s | 200 y `accessToken` con forma de JWT |
| `nsv-stations` | Catálogo de estaciones | GET `https://api.rsv.renfe.com/catalog/masterdata/v1/stations` con cabeceras de sesión anónima | 15 min | 10 s | > 3 s | 200 y lista no vacía |
| `nsv-search` | Búsqueda de viajes | POST `https://api.rsv.renfe.com/browsing/traveloptions/v1/search-travel`, ruta fija Madrid y Barcelona | 15 min | 15 s | > 5 s | 200 y lista de viajes (puede estar vacía si la fecha no tiene trenes; ver incertidumbre 3) |
| `legacy-shop` | Venta clásica | GET `https://venta.renfe.com/vol/buscarTren.do?Idioma=es&Pais=ES` + POST DWR `__System.generateId.dwr` | 15 min | 15 s | > 6 s | 200 en ambas y `handleCallback` con id de sesión |
| `live-map` | Mapa en vivo larga distancia | GET `https://tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json` | 1 min | 10 s | > 2 s, o vacío entre 7:00 y 23:00 (Madrid) | 200 y JSON con la forma del mapa |
| `gtfs-avld` | Horarios GTFS AV/LD | GET condicional `https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip` con `If-None-Match` | 15 min | 20 s | > 5 s hasta cabeceras | 200 o 304 |
| `www-search` | Buscador de renfe.com | GET `https://www.renfe.com/es/es/buscador-billetes` | 5 min | 10 s | > 3 s | 200 y HTML del buscador |

Notas que vienen de `renfe-cli` y condicionan el diseño:
- El autor de `renfe-cli` anotó que el mapa en vivo rechazó conexiones desde España durante más de 2 horas el 17 de noviembre, y que el 18, comprobado cada 15 minutos, cortó una vez durante menos de un minuto. Por eso el mapa se sondea cada minuto: con 15 minutos esa caída corta no se habría visto bien.
- El mapa tiene `Cache-Control: max-age=30`: sondear más de una vez por minuto no aporta nada.
- Renfe tiene dos sistemas de venta hasta principios de 2027: la venta nueva vende viajes desde el 25 de enero de 2027. La sonda `legacy-shop` tendrá `retired_at` cuando la venta clásica desaparezca, y la web la mostrará como "retirada", no como caída.
- `renfe-cli` trata una página HTML a cualquier código como protección antibots. Aquí eso es `blocked`, nunca `down`.
- Los umbrales de degradado son de partida. Se recalibran en M5 con una semana de datos reales.

Presupuesto por hora con este catálogo: config 12, token 12, estaciones 4, búsqueda 4 (reutiliza el token vigente), venta clásica 8 (dos peticiones), mapa 60, GTFS 4, renfe.com 12 = **116** peticiones a Renfe, más unas 12 al endpoint de control.

## 7. Modelo de datos (Supabase)

```
probes      (id text pk, name, group_name, host, method, url_display, interval_s, timeout_s,
             degraded_ms, enabled bool, retired_at timestamptz null, sort int)
checks      (id bigint pk, probe_id fk, started_at timestamptz, duration_ms int,
             http_status int null, outcome outcome_enum, reason text, region text,
             probe_version text)
incidents   (id bigint pk, probe_id fk, kind outcome_enum, started_at, ended_at null,
             checks_count int)
heartbeat   (region text pk, last_seen timestamptz, probe_version text)
```

Vistas públicas (la web solo lee estas): `v_status_now`, `v_uptime_windows` (24 h, 7, 30 y 90 días, con uptime, nueves y segundos por estado), `v_daily_90` (peor estado y uptime por día), `v_latency_24h` (p50 y p95 cada 30 minutos), `v_recent_checks` (últimas 50 por sonda, sin `reason` interno si se decide), `v_incidents`.

- RLS: `anon` solo puede `select` sobre las vistas. Ninguna tabla es escribible con la clave anónima. La sonda escribe con la `service_role`, que solo existe en el entorno del VPS.
- Retención: `checks` crudos 120 días; rollups diarios para siempre.
- Volumen estimado: unas 2.900 comprobaciones al día, unas 350.000 en 120 días. Cabe de sobra en el plan gratuito, pero se confirma en M3.

## 8. Feature Map inicial

El agente crea `docs/feature-map.md` en M0 con estas entradas y lo completa según se construye:

| Feature | Qué es (punto de vista del usuario) | Ubicación | Notas |
|---|---|---|---|
| `status-overview` | Portada con el uptime agregado, los nueves, la escala y la lista de servicios | `web/src/features/status-overview/` | Tabs 24h, 7d, 30d, 90d; artboard "Inicio" |
| `service-detail` | Detalle de un servicio: ventanas, latencia, 90 días, reglas y últimas comprobaciones | `web/src/features/service-detail/` | Ruta `/servicio/:id`; artboard "Detalle de servicio" |
| `methodology` | Cómo se mide, estados, fórmula, catálogo y límites | `web/src/features/methodology/` | Ruta `/metodologia`; el catálogo se lee de `probes`, no se escribe a mano |
| `incidents` | Lista de incidentes recientes | `web/src/features/incidents/` | Sección de portada y ancla `#incidentes` |
| `probes` | Una comprobación por servicio de Renfe | `prober/src/anden9/probes/` | Ver sección 6 y `docs/probes.md` |
| `classifier` | Convierte una respuesta en un estado | `prober/src/anden9/domain/classifier.py` | Riesgo alto en RDD |
| `incident-tracker` | Abre y cierra incidentes | `prober/src/anden9/domain/incidents.py` | Riesgo alto en RDD |
| `scheduler` | Decide cuándo se ejecuta cada sonda y aplica el presupuesto | `prober/src/anden9/scheduler.py` | Riesgo alto en RDD |
| `store` | Escribe en Supabase | `prober/src/anden9/adapters/store_supabase.py` | Única escritura a la base de datos |
| `db-views` | Agregados públicos | `supabase/migrations/` | La fórmula canónica vive aquí |

## 9. Metodología: ODD aplicada a este proyecto

Se trabaja con **Organic Driven Development** de gentle-ai, ejecutado en gentle-shell. Cada petición de implementación recorre los siete pasos; el trabajo pequeño se mantiene ligero y el sustancial deja un único documento de feature recuperable entre sesiones.

| Paso ODD | Aplicación en este proyecto |
|---|---|
| 1. Authorize | Preguntas, revisiones y propuestas son solo lectura. Se modifica código solo cuando Albert pide un cambio |
| 2. Explore | Leer el código y los docs afectados y, para cada sonda, el fichero de `renfe-cli` correspondiente |
| 3. Resolve uncertainty | Resolver las incertidumbres de la sección 9.1 **investigando u observando**, nunca suponiendo |
| 4. Classify | Pequeño (cambio entendido y localizado) frente a sustancial (varias features, contrato nuevo, migración o área de riesgo alto) |
| 5. Track | Solo si es sustancial: un documento de feature en `odd/` con tareas y estado |
| 6. Implement | Tarea a tarea, copiando la plantilla canónica (`probes/_template.py`, `web/src/features/_template/`) |
| 7. Close | Cierre con prueba verificada: salida de tests, salida de `anden9 probe once`, capturas de Playwright y comprobaciones estáticas en verde |

### 9.1 Incertidumbres que hay que resolver antes de asumir

1. **Región y proveedor de la sonda.** ¿Responde Renfe igual desde un VPS que desde una conexión doméstica? ¿Bloquea IPs de datacenter? Se mide en M2 ejecutando `anden9 probe once --all` desde el VPS candidato y desde local, y se compara.
2. **Sesión anónima de la venta nueva.** Qué cabeceras exige cada endpoint (`session-id`, `x-terminal-id`, `origin`, `referer`) y cuánto dura el token. Leer `client.py` de `renfe-cli` y confirmarlo observando.
3. **`search-travel` antes del 25 ene 2027.** ¿Devuelve horarios para fechas anteriores a que la venta nueva venda? Elegir la fecha de la ruta fija según lo observado y documentarlo en `docs/probes.md`.
4. **Venta clásica mínima.** Cuál es la secuencia más corta que demuestra que el buscador funciona sin hacer una búsqueda completa.
5. **Mapa en vivo de noche.** A qué horas está vacío de forma normal. Observar una noche completa antes de fijar la ventana de "vacío = degradado".
6. **GTFS condicional.** ¿`ssl.renfe.com` devuelve `ETag` y 304? Si no, usar `HEAD` o `Range` y documentarlo.
7. **Umbrales de degradado.** Calibrar con una semana de datos (p95 base por servicio).
8. **Términos de uso de Renfe** sobre acceso automatizado: lo revisa Albert. Es una decisión humana; el agente solo deja el enlace y un resumen.
9. **Endpoint de control.** Confirmar que el elegido responde de forma estable desde el VPS.
10. **Límites del plan gratuito de Supabase** (tamaño, pausa por inactividad) con el volumen de la sección 7.

Cada una se cierra con una nota en el documento de feature correspondiente, con la evidencia (comando y salida).

### 9.2 Clasificación de los hitos

Todos los hitos de la sección 12 son sustanciales y llevan documento de feature propio. Los ajustes posteriores (un umbral, un texto, un color) son pequeños y no necesitan documento.

## 10. Metodología: RDD (Receipt-Driven Development)

RDD es la revisión nativa de gentle-ai: tras cada commit de una unidad de trabajo, el cambio exacto se congela, se evalúa su riesgo y se revisa con la profundidad adecuada (pasiva sin lentes, media con una lente, alta con las cuatro: **Risk, Resilience, Readability, Reliability**). Se permite como máximo una corrección acotada y un reconocimiento exacto cierra la transacción. **La entrega sigue siendo de Albert.**

Reglas:
- En la versión actual de gentle-ai, RDD viene **activado por defecto** y se desactiva con `gentle-ai review mode disable`. El interruptor es de Albert: los agentes no lo activan ni lo desactivan. Al empezar consultan `gentle-ai review mode status --cwd .` y lo anotan en el PR (`RDD: on/off`).
- Si está activo, tras cada commit de unidad de trabajo se evalúa el rango no revisado.
- Los elementos de **riesgo alto** exigen verificador independiente, escribiera quien escribiera el cambio.

Mapa de riesgo de este proyecto:

| Nivel | Áreas | Qué miran las lentes |
|---|---|---|
| Alto | `scheduler` (frecuencias, presupuesto, `Retry-After`), user agent y cabeceras de las sondas, `classifier` y `incident-tracker`, vistas SQL con la fórmula, migraciones y RLS, manejo de secretos (`service_role`, clave y token de Renfe) | Risk: credibilidad de los datos publicados, permisos y secretos. Resilience: fallos de red, huecos, reinicios. Reliability: la matemática que fijan los tests |
| Medio | Parsers de cada sonda, capa `web/src/data/`, formateo de cifras | Una lente enfocada según el cambio |
| Pasivo | Estilos, textos, documentación, tests, refactors sin cambio de comportamiento | Lectura estructural |

## 11. Flujo Git

```
main  <-- Albert, a mano
  ^
 dev  <-- Albert, a mano (merge de los PR)
  ^
feat/<slug>  fix/<slug>  chore/<slug>   <-- agentes
```

- Los agentes ramifican **desde `dev`**, hacen commits atómicos con Conventional Commits (`feat(probes): add live-map probe`), hacen push y abren un PR hacia `dev`.
- Los agentes **no hacen merge** de nada y nunca hacen push a `main` ni a `dev`.
- Un PR por unidad coherente; debe poder entenderse y revertirse de forma aislada.
- Cada PR incluye: qué y por qué (con enlace al issue), cómo se verificó (comandos y salida), qué **no** se verificó, si se actualizó el Feature Map, nueva restricción propuesta (si aplica) y estado de RDD.

## 12. Plan por hitos

Cada hito es una unidad ODD con su documento de feature. Los criterios de aceptación son comprobables; si el agente no puede comprobar uno, lo dice explícitamente.

### M0: Andamiaje y restricciones
- Monorepo con `prober/` (uv, ruff, mypy, pytest, import-linter) y `web/` (pnpm, Vite, TS estricto, ESLint, Vitest, Playwright, dependency-cruiser), `supabase/` inicializado.
- Script raíz: `make check`, que ejecuta todo, más `scripts/repo-hygiene` y `scripts/request-budget`.
- Plantillas canónicas: `prober/src/anden9/probes/_template.py` y `web/src/features/_template/`.
- `docs/feature-map.md`, `docs/runbook.md`, `docs/glossary.md`, `docs/probes.md`.
- CI en GitHub Actions para PRs hacia `dev`.
- **Aceptación:** `make check` en verde en una rama limpia; una importación prohibida de prueba (dominio importando `httpx`) hace fallar import-linter; un intervalo de 30 s en el catálogo hace fallar el test de presupuesto.

### M1: Dominio de medición (sin red)
- `Outcome`, `classifier`, `incident-tracker`, cobertura de intervalos y huecos.
- `contracts/uptime_cases.json` con casos de referencia (sin caídas, todo bloqueado, ventana insuficiente, truncado de 99,996 %, 1 a 5 nueves).
- **Aceptación:** tests con hypothesis para las propiedades (el uptime nunca sale de [0, 1], bloqueado y sin datos nunca bajan el uptime, 2 fallos abren y 2 éxitos cierran). Todos los casos del contrato pasan.

### M2: Sondas reales y scheduler
- Adaptador `httpx`, las 8 sondas de la sección 6, el endpoint de control, el scheduler con presupuesto y `Retry-After`.
- CLI: `anden9 probe once <id>` y `anden9 probe once --all`, que imprimen el resultado sin escribir en base de datos.
- Tests con respuestas grabadas (respx) para cada estado de cada sonda, incluidas una página HTML de protección y un 429.
- **Aceptación:** `anden9 probe once --all` contra Renfe real devuelve un resultado por sonda y se pega en el PR. Se resuelven las incertidumbres 1 a 6 y 9. **Riesgo alto en RDD.**

### M3: Persistencia y vistas
- Migraciones de la sección 7, RLS, vistas, retención; adaptador `store_supabase`; heartbeat.
- Los casos de `contracts/uptime_cases.json` se ejecutan contra las vistas en un Supabase local (`supabase start`).
- **Aceptación:** con la sonda corriendo 30 minutos contra un Supabase local, las vistas devuelven datos coherentes; un test demuestra que la clave anónima no puede escribir en ninguna tabla ni leer tablas crudas. Se resuelve la incertidumbre 10. **Riesgo alto en RDD.**

### M4: Web
- Las cuatro pantallas del diseño, responsive, leyendo solo de las vistas; estados de carga, error y "sin datos".
- `supabase/seed/` con datos de ejemplo para desarrollo y e2e.
- **Aceptación:** Playwright recorre portada, cambio de ventana, detalle de servicio y metodología con datos semilla, en escritorio (1440) y móvil (390), con capturas adjuntas al PR; axe sin violaciones serias; el aviso "No oficial" aparece en todas las rutas.

### M5: Despliegue y operación
- Imagen Docker de la sonda, unidad systemd, variables de entorno, rotación de logs; despliegue de la web en Netlify.
- Alerta mínima para Albert si el heartbeat tiene más de 10 minutos (por ejemplo, la propia web muestra un banner y un workflow programado abre un issue).
- `docs/runbook.md` completo: arrancar, parar, actualizar, rotar claves, qué hacer si Renfe bloquea la sonda.
- **Aceptación automática:** el agente prepara todo y lo prueba en local con Docker. **Aceptación manual (solo Albert):** crear el VPS, poner los secretos y desplegar; el agente deja la lista de pasos y declara qué no pudo verificar. Tras 7 días, recalibrar umbrales (incertidumbre 7) con datos reales.

## 13. Estrategia de verificación (cuatro niveles)

1. **Nivel 1, sin red:** tests unitarios, de contrato y con HTTP grabado. Lo ejecuta el agente siempre.
2. **Nivel 2, Renfe real sin base de datos:** `anden9 probe once`. Lo ejecuta el agente como mucho **una vez cada 5 minutos** y nunca en bucle; el presupuesto de la sección 5.4 también le aplica.
3. **Nivel 3, pila local:** Supabase local + sonda en bucle con un catálogo reducido (solo `live-map` y `www-search`) + web en dev + Playwright.
4. **Nivel 4, producción:** solo Albert (VPS, secretos, despliegue).

## 14. Riesgos

| Riesgo | Mitigación |
|---|---|
| Publicar caídas falsas y perder credibilidad | Estados `blocked` y `unknown` fuera del denominador, endpoint de control, 2 fallos para abrir incidente, metodología pública |
| Renfe bloquea la sonda | Se muestra como "bloqueado", no como caída; user agent honesto; presupuesto bajo; nunca se intenta saltar el bloqueo |
| Renfe cambia endpoints o formatos | Un `bad_shape` sostenido abre incidente y aparece en el runbook como "revisar la sonda"; leer los cambios de `renfe-cli` |
| La sonda deja de medir sin que nadie se entere | Heartbeat, banner en la web y alerta a Albert |
| Confusión con Renfe o problemas de marca | Paleta y nombre propios, aviso "No oficial" en todas las páginas, sin logos de Renfe |
| Términos de uso de Renfe | Lo revisa Albert antes de publicar (incertidumbre 8) |
| Sesgo regional | Mostrar desde dónde se mide en la web y en la metodología |

## 15. Definición de hecho para v1

- [ ] M0 a M5 cerrados con prueba verificada en cada PR.
- [ ] `make check` en verde en `dev`.
- [ ] Todas las restricciones de las secciones 5 y 5.4 cubiertas por tests o comprobaciones automáticas.
- [ ] `docs/feature-map.md`, `docs/probes.md` y `docs/runbook.md` al día.
- [ ] Despliegue manual hecho por Albert y 7 días de datos reales en la web.
- [ ] Umbrales recalibrados con datos reales.

## 16. Prompt de arranque para el agente

Pegar en gentle-shell tras crear el repo con `main` y `dev`, y con `AGENTS.md` y este `BRIEF.md` en la raíz:

```
Lee AGENTS.md y BRIEF.md completos. Trabaja con ODD y respeta el flujo Git
(ramas desde dev, PR hacia dev, sin merges).

1. Consulta el estado de RDD con `gentle-ai review mode status --cwd .` y
   dímelo; no lo cambies tú.
2. Clona https://github.com/luisgonzaleznf/renfe-cli en una carpeta fuera
   del repo, solo para leerlo (no lo ejecutes ni copies sus datos), y
   resume en docs/probes.md qué hace cada endpoint de la sección 6.
3. Empieza por el hito M0 (andamiaje y restricciones). Es una tarea
   sustancial: crea su documento de feature en odd/ y avanza tarea a tarea.
4. Al cerrar M0, abre el PR hacia dev con la evidencia de `make check` y
   párate: no empieces M1 hasta que yo haya hecho el merge.
```
