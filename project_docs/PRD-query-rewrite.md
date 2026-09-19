# PRD: Query rewrite, relative cutoff, citation override

**Status:** Implemented  
**Date:** 2026-09-19  
**Branch:** `feat/query-rewrite-relative-cutoff`

## Problem

Casual questions such as “review the documents and the evidence supporting their hypotheses, what hypotheses have the strongest hypotheses” do not live in the same MiniLM neighborhood as paper paragraphs. A 0.4 cosine cliff dropped real hits (~0.18–0.35). Nearest-k then ranked bibliography (zero-width-space DOIs, PubMed lines, numbered refs) that ingest had labeled `context`. The chat model refused, and canned replies stored no sources — so it looked like “nothing in your documents.”

This product is mixed-corpus (papers, news, notes). Paper-only aliases (`we hypothesize`, `we found`) and “rewrite as a scientific abstract” are the wrong default.

## Goal

Close the word-mismatch on the **query path** with no schema change and no re-ingest.

1. Rewrite the question in **these documents’** vocabulary (thread title, file names, headings).
2. Retrieve a wide nearest-N every time; keep hits within ~0.15 of the best cosine.
3. Hard-drop only citation and boilerplate. Roles otherwise boost.
4. Reclassify bibliography at query time even when stored role is `context`.
5. Grade leftover chunks; expand short title hits to neighbors.
6. Retry once with rewrite + aliases before the canned line.

## Non-goals (this branch)

- OpenClaw / multi-agent wrappers
- SPECTER, IMRaD routing, HyDE-as-abstract
- pgvector dimension change
- Ingest characterization, FTS, BGE-small re-embed (later)

## Success

- Unit: parse two HyDE registers (news lede + plain note); relative cut keeps 0.28 when best is 0.31; zwsp DOI / PubMed / numbered-ref heading → citation even if stored `context`; method/experience never excluded.
- UAT: fixture with review lede + hypothesis + zwsp bibliography; evidence/review question sources are not PubMed/DOI soup.
- Dogfood: same-thread follow-up “review the documents / strongest hypotheses” returns an answer with sources, not only the canned line.
