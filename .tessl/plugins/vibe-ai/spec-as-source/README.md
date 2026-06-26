# vibe-ai/spec-as-source

Enforcement meccanico per lo **spec-as-source** sopra il plugin `tessl-labs/spec-driven-development`.

Il plugin spec-driven porta un progetto a *spec-anchored* (la spec prima del codice), ma non verifica nulla. Questo plugin aggiunge gli strumenti che rendono la spec un **vincolo strutturale**: script di verifica, ownership dei file, workflow CI e le skill che li orchestrano.

---

## Installazione

```bash
# nel tuo progetto (dopo tessl init)
tessl install tessl-labs/spec-driven-development   # il processo
tessl install vibe-ai/spec-as-source               # l'enforcement
```

Richiede: progetto inizializzato con `tessl init`, `git`, e un test runner (pytest / vitest / jest / cargo / go).

---

## Cosa installa

### Rule (sempre attive)

| Rule | Comportamento imposto |
|---|---|
| `spec-as-source` | L'implementazione non è completa finché tutti i `[@test]` esistono; un `targets` non cambia senza la sua spec |
| `generated-file-header` | Ogni file `targets` inizia con `# GENERATED FROM SPEC` |

### Skill (on-demand)

| Skill | Quando usarla | Comando |
|---|---|---|
| `spec-as-source-setup` | una volta, per creare script + CI + pre-commit | `Use spec-as-source-setup.` |
| `spec-verify` | a ogni giro, per verificare spec/test/codice | `Use spec-verify.` |
| `spec-ci-sync` | dopo aver aggiunto una spec o cambiato stack | `Use spec-ci-sync.` |
| `spec-rebuild` | per dimostrare che le spec sono la sorgente | `Use spec-rebuild.` |

### Docs

`policy.md` — la policy in chiaro: ruoli, livelli di enforcement, cosa significa spec-as-source qui.

---

## Uso tipico

```text
# 1. una tantum: genera l'infrastruttura di enforcement
Use spec-as-source-setup.

# 2. allinea la CI al tuo stack
Use spec-ci-sync.

# 3. a ogni ciclo di lavoro, dopo aver implementato
Use spec-verify.
```

Cosa crea `spec-as-source-setup` nel progetto:

```text
scripts/check-spec-links.sh          # ogni [@test] punta a un file esistente
scripts/check-target-ownership.sh    # un target non cambia senza la sua spec
scripts/build-spec-manifest.py       # mappa spec → requisiti → target → test
scripts/verify.sh                    # esegue i tre script + test suite
.pre-commit-config.yaml              # gli stessi check in locale
.github/workflows/spec-verification.yml  # gli stessi check in CI
```

---

## I 4 controlli di `spec-verify`

Eseguiti in sequenza, sono gli stessi che girano in CI:

| # | Controllo | Se fallisce | Recupero |
|---|---|---|---|
| 1 | `check-spec-links` | un `[@test]` punta a un file inesistente | crea il file di test mancante |
| 2 | `check-target-ownership` | un `targets` è cambiato senza la sua spec | annulla la modifica → aggiorna la spec → rigenera dalla spec |
| 3 | `build-spec-manifest` | una spec non è parsabile | correggi frontmatter / header dei requisiti |
| 4 | test suite | il comportamento contraddice la spec | allinea il codice, o cambia prima la spec |

Il controllo #2 è il cuore dello spec-as-source: è ciò che un progetto "normale" non ha.

---

## Aggiornamento

```bash
tessl update vibe-ai/spec-as-source
# poi RIAVVIA Claude Code: le skill si caricano all'avvio della sessione
```

Se `tessl update` non vede il plugin, non è registrato in `tessl.json`: installalo prima con `tessl install vibe-ai/spec-as-source`.

---

## Convenzioni delle spec

Perché gli script funzionino, ogni `.spec.md` deve avere:

```markdown
---
name: <nome>
description: <una riga>
targets:
  - ../src/percorso/file.py      # i file che questa spec possiede
---

## REQ-AREA-001 — Titolo del requisito
Descrizione. `[@test] ../tests/percorso/test_file.py`
```

- frontmatter con `targets` (dichiarazione di proprietà);
- requisiti con ID stabile `REQ-<AREA>-<NNN>` (header `##` o `###`);
- ogni requisito con almeno un `[@test]` verso un file di test.

---

## Autore

Workspace `vibe-ai`.
