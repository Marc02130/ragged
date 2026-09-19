# PRD: Chunk roles for retrieval

**Status:** Shipped (roles now act as boosts; citation/boilerplate remain default exclusions)
**Date:** 2026-09-17  
**Branch:** `feat/chunk-roles`

## Problem

Follow-up questions such as “what hypotheses have the best evidence” either miss the cosine cutoff or retrieve the **wrong kind** of text (reference lists, ANOVA boilerplate, taxon dumps). The model then answers with the canned refusal even though the PDFs contain hypotheses and findings.

This product is not academic-only. Users upload papers, newspaper/magazine articles, personal writing, and reports. A closed IMRaD section list (Introduction / Discussion) is too narrow.

## Goal

Label every **chunk** with a role. Classify the **question** into the same roles. Retrieve only matching chunks. Drop citation and boilerplate unless the user asks for them.

Descriptions of the roles are the contract: they are used to label chunks, to route queries, and to explain the system in the UI later.

## Roles

| Role | Description |
| --- | --- |
| **claim** | What the author asserts, argues, hypothesizes, or believes. Opinions, theses, “I think…”, “we propose…”, editorial line. |
| **finding** | What is reported as observed or having happened: results, facts, events, measurements, “sales rose…”, “the court found…”. |
| **evaluation** | Judgment of strength or meaning: limitations, “unconfirmed”, “strongest evidence”, doubt, “more research needed”. |
| **method** | How it was done or known: instruments, protocol, sources, recipe, interview method, statistics. |
| **context** | Background the reader needs: setting, prior story, definitions, literature *narrative in the body* (not a reference list). |
| **experience** | First-person lived detail: diary, memoir, anecdote, travel notes. |
| **citation** | Pointers to other works: bibliography, “see Smith 2019”, URL/DOI dumps, footnote-only references. |
| **boilerplate** | Funding, ads, headers, acknowledgements, data-availability one-liners, cookie copy. |

## Query routing

| User ask | Retrieve |
| --- | --- |
| Default / “what does this say” | claim, finding, evaluation, experience, context |
| Hypotheses, mechanisms, “they argue” | claim, context, evaluation |
| Best evidence, strongest support | finding, evaluation, claim |
| How / instrumentation / protocol | method |
| How I felt, what happened to me | experience, context |
| References / citations | citation |

Never send `citation` or `boilerplate` for default science/news/personal Q&A.

## Optional file type (phase 2)

`article` | `academic` | `personal` | `report` | `other` — not required for v1. Chunk roles already cover mixed corpora.

## Non-goals (v1)

- User-editable taxonomies
- LLM-only labeling that requires a chat key at ingest
- Replacing vector search (roles **filter**, they do not replace embeddings)
- Auto-delete of unlabeled historical chunks

## Success

- Unit: “best evidence” maps to finding+evaluation+claim; bibliography text maps to citation and is not returned.
- UAT: upload a fixture with a References block + a hypothesis paragraph; evidence query sources are not the reference block.
- Dogfood: same-thread follow-up after a mechanisms question returns an answer with sources, not only the canned line.
- Existing papers without labels still work: unlabeled chunks are classified at query time from text (heuristics + descriptions).
