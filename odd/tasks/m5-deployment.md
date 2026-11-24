# M5: deployment and operation

Feature document for milestone M5 of `BRIEF.md` section 12. Everything here is prepared and tested
locally by the agent; the VPS, the cloud project and Netlify belong to Albert.

## Specs

S1 (scope, verbatim from `BRIEF.md` §12):

> - Imagen Docker de la sonda, unidad systemd, variables de entorno, rotación de logs; despliegue de la web en Netlify.
> - Alerta mínima para Albert si el heartbeat tiene más de 10 minutos (por ejemplo, la propia web muestra un banner y un workflow programado abre un issue).
> - `docs/runbook.md` completo: arrancar, parar, actualizar, rotar claves, qué hacer si Renfe bloquea la sonda.

S2 (acceptance, verbatim):

> **Aceptación automática:** el agente prepara todo y lo prueba en local con Docker. **Aceptación manual (solo Albert):** crear el VPS, poner los secretos y desplegar; el agente deja la lista de pasos y declara qué no pudo verificar. Tras 7 días, recalibrar umbrales (incertidumbre 7) con datos reales.

S3 (secrets, verbatim from `AGENTS.md` §5.1): the `service_role` key is read only by
`prober/src/anden9/config.py`, never in the web bundle, never versioned.

## Tasks

| ID | Task | Specs | Commit |
| --- | --- | --- | --- |
| T1 | Prober image, non-root, dependencies cached in their own layer, `.dockerignore` | S1 | `feat(deploy): add the prober image` |
| T2 | Compose file, systemd unit and the host variables example | S1, S3 | `feat(deploy): add the compose file and the systemd unit` |
| T3 | Netlify configuration for the SPA | S1 | `feat(deploy): add the Netlify configuration` |
| T4 | Scheduled heartbeat workflow that opens an issue after ten silent minutes | S1 | `feat(ci): watch the prober heartbeat` |
| T5 | Runbook: start, stop, update, rotate keys, what to do when Renfe blocks the sensor | S1 | `docs(runbook): cover deployment and operation` |
| T6 | Local proof: build the image, run it, run one probe from inside the container | S2 | evidence in this document |

## Log

### L1 (original request, verbatim)

> ok continua y no pares hasta tenerlo todo terminado. No preguntes a no ser que sea necesario. Y RDD tambein permitido. No pares

### L2 (decisions)

- **The image carries no secret and no configuration.** Everything arrives through the host
  variables file, so the same image is the one Albert runs and the one tested here.
- **The unit runs compose, not a bare `docker run`.** One place defines the container, and the log
  rotation lives with it.
- The workflow is inert until Albert adds the two Supabase secrets; it says so in its log instead of
  failing red every fifteen minutes.
