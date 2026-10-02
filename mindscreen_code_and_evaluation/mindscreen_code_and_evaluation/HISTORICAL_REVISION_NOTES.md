# MindScreen: historical revision notes

> Archived provenance only. These notes describe the pre-reconciliation ZIP and its former `patches/` directory. The patches have since been integrated and removed; use the repository root README for current instructions.

These notes go with `mindscreen_revised.pdf` and `mindscreen_revised.tex`.

All new numbers in the paper come from code that was actually run, and all of that code is in `mindscreen_code_and_evaluation.zip`. Every reference was checked against a publisher page, DOI record, PubMed/Europe PMC, the ACL Anthology, arXiv or an official government page.

---

## 1. Read this first: problems found in your public repository

While checking the paper, we found that your full project is public at `github.com/ruchita0131/mindscreen` (a fork is at `github.com/shravyas841/mindscreen`). Fix the items below **before you submit anything**.

| # | Problem | Why it matters | What to do |
|---|---|---|---|
| 1 | `mindscreen_ieee_paper.tex` and `mindscreen_ieee_research_paper.md` (the old paper) are public. | iThenticate/Crossref Similarity Check will report the old version as a near-100% match. That looks like duplicate publication. | Make both repositories private, or delete those files **and rewrite the git history**. Deleting the files in a later commit does not remove them from the history. |
| 2 | `train_daicwoz_audio.py` loads real DAIC-WOZ labels and then **generates the acoustic features with `np.random`** for each severity class. | Reporting any result from this script would be data fabrication. The paper does not use it, and must never use it. | Delete the script. Do not report any "DAIC-WOZ" audio result unless it is computed from the real licensed features. |
| 3 | `daic_woz_features/covarep/*.csv` are HTML error pages, not features. `daic_woz_features/labels/` contains real DAIC-WOZ/E-DAIC label files. | The DAIC-WOZ licence allows distribution to approved researchers only. Posting the labels publicly may breach it. | Remove the labels from the public repository and its history. |
| 4 | `benchmarks/EVIDENCE_AUDIT_REPORT.md` says all 16 references were "verified". | They were not. [6] was in the wrong venue, [9] (Yang/Jiang/Cambria, IEEE TAC 2023) could not be found anywhere, [11] had the wrong first initial, and [2] had the wrong publication number. | Do not rely on that report. Section 5 below gives the checked reference list. |
| 5 | The old paper's numbers do not match your own raw benchmark files. | The paper said 13.2 ms for the local path, 8.4 ms for acoustic scoring and 1.2 ms for PHQ, measured on a 0.5 vCPU container. `benchmarks/raw_latency_measurements.json` says 0.57 ms, 0.17 ms and 0.03 ms, measured on Windows. Table IV of the old paper (TC-1 "Mild", TC-2 S=3, TC-3 "Mild") contradicts `hre_masking_scenarios_raw.json` (minimal, S=2, already c3). No raw data exist for the 480 / 390 / 512 ms API figures. | The revised paper drops all unsupported numbers and reports only what was measured. |
| 6 | `backend/mental_health.db` (a SQLite file with 1 user and 1 assessment) and `frontend/.env.production` are committed. | They may hold personal data or deployment configuration. | Remove them from the repository and its history. Rotate any secrets they contained. |
| 7 | `routers/chat.py` still lists the KIRAN helpline. | News reports (Nov 2024) say KIRAN was merged into Tele-MANAS. We could not find an official notice. | Show Tele-MANAS (14416 / 1-800-891-4416) as the primary number. |

---

## 2. What changed in the paper, by reviewer comment

| Review comment | Change made |
|---|---|
| M1: novelty overstated, "formally verified" | "Formally specified and verified" is gone. The paper now says the escalation rules apply established clinical practice (Joint Commission SEA 56, NIMH ASQ). The contribution is recast as integrating those rules and measuring how they behave. Related work now covers NegEx, ConText, clinical decision support and LLM guardrails. |
| M2: evaluation only tests the code path | Added a **real-data evaluation** on two public corpora: the SDCNL test split (379 Reddit posts) and a tweet corpus (8,785). It uses sensitivity, specificity and PPV with Wilson 95% CIs, exact McNemar tests, a learned baseline, an ablation and a breakdown of the misses. Added a design-space analysis of fusion against the PHQ-9 tier. |
| M3: negation window creates false negatives | Confirmed on real data. The deployed filter (v1) found only **22.8% / 24.2%** of positive posts. Among posts that contained a trigger phrase, message-wide third-party suppression caused most of the misses. A clause-scoped filter based on ConText (v2) reached **55.4% / 51.3%**. Adversarial cases such as "I'm not okay, I want to kill myself" were added to the suite. |
| M4: "hopeless" is not suicidal intent | Distress words now raise the text tier to moderate but no longer set the crisis flag. Self-harm statements do set the crisis flag in the released version, v2.1. S2 was relabelled. |
| M5: weights, PHQ subordinate, S≥20 vs S≥15 | We proved analytically that PHQ-9 alone cannot overturn the text branch when the text top score s > 0.288. We quantified under-triage at **37.0% / 55.3% / 85.2%** for the mild, moderate and moderately-severe bands. The S≥20 rule was replaced by a **PHQ-9 tier floor (R0)**. A modality ablation was added. |
| M6: Table V inconsistent | Recomputed. The table now shows the pre-override class, the raw maximum **and** the softened score. It also explains that the old text vectors were the keyword-fallback vectors. |
| M7: audio confounds (AGC, sample rate) | Documented. The patched client disables AGC, noise suppression and echo cancellation. The paper states which of the six features have literature support and which do not (ZCR, centroid and rolloff have none). The byte-scaled, dB-mapped analyser spectrum is also disclosed. |
| M8: missing audio | Found that the deployed web client **never** treated audio as missing: it sent fixed "neutral" features that score as moderate-leaning. The patch sends null, and the server renormalises the weights. |
| M9: privacy overclaims | "Without PII" and "complete continuity offline" are removed. Added the DPDP Act 2023 and the DPDP Rules (notified 14 Nov 2025), plus an ethics statement. |
| M10: latency claims | Replaced with measured server-side compute latency: 0.45 ms mean per real post for the local pipeline, on 1 pinned core. The hardware is disclosed. API latencies are not reported because no raw data exist. |
| Minor: notation, Eq. 4, Eq. 8, Table I, abstract, disclaimers, references | Symbols are now distinct (x for text, T for temperature, ᵀ removed). Γ is documented. The temperature step is written as p^(1/T) and stated to be monotone. Table I was redesigned with task, data and evaluation columns. The abstract is 248 words. The repeated disclaimers are consolidated. Added an architecture figure and a results figure. References went from 16 to 61. The capstone note moved to the Acknowledgment. |

---

## 3. Code changes you must merge (otherwise the paper does not describe your system)

These are in `patches/` inside the zip. Each is a drop-in replacement for the file at the same path in your repository.

| File | Change |
|---|---|
| `backend/services/negation_service.py` | Crisis filter v2.1 (clause-scoped, with self-harm triggers). It keeps the old return keys, so no caller changes are needed. |
| `backend/services/fusion_service.py` | Renormalises weights over the modalities present. Drops the base64 payload-size audio "proxy". Adds R0 (PHQ-9 floor), R1 (Item 9) and R2 (crisis text). |
| `backend/services/ml_service.py` | Distress words raise the text tier to at least moderate but do not set the crisis flag. |
| `frontend/src/pages/Assessment.tsx` | Turns off `autoGainControl`, `noiseSuppression` and `echoCancellation`. Sends `null` when audio is skipped. |
| `frontend/src/utils/audioFeatures.ts` | Returns `null` for recordings that are too short, instead of neutral features. |

We ran a smoke test of the patched backend (5 scenarios) and confirmed the patched filter gives identical results to the evaluated v2.1 on all 9,164 test texts. The frontend patch was not compiled here; run `npm run build`.

---

## 4. Things only you can do

1. **Repository URL.** The Data and Code Availability section shows a red placeholder. Create a *clean* public repository containing the `evaluation/` folder and the patched system, then put its URL there.
2. **Target venue.** The paper uses the IEEE Transactions (`IEEEtran`, journal mode) template. If you choose IEEE Access or IEEE JBHI, move the content into that journal's own template and check its abstract limit. IEEE Access allows up to 250 words; ours is 248.
3. **Official plagiarism check.** We could only do a web spot-check (Section 6). Run iThenticate through your institution **after** taking the old paper off GitHub.
4. **Author e-mails.** The four student addresses were expanded from the old header's `{…}@gmail.com` pattern (for example `shravya.sanikere@gmail.com`, `apoorva.k@gmail.com`). Please confirm each one.
5. **Optional strengthening, needed for a Transactions-level journal.** Request DAIC-WOZ/E-DAIC access at https://dcapswoz.ict.usc.edu/ (academic e-mail and signed EULA). Then evaluate the audio branch on the real COVAREP/eGeMAPS features, and the emotion branch on the transcripts.

---

## 5. Reference verification

Status key: **V** = verified against the source listed. **C** = corrected (the error found is in the "Correction" column). **R** = replaced.

| Old ref | Status | Correction / source |
|---|---|---|
| [1] WHO fact sheet, Mar 2023 | C | The current sheet is dated 11 Sep 2026: 5.2% of adults, about 322 million people, 727,000 suicides in 2021. The sheet no longer says "leading cause of disability". That claim now cites the WHO news release of 30 Mar 2017. https://www.who.int/news-room/fact-sheets/detail/depression · https://www.who.int/news/item/30-03-2017--depression-let-s-talk-says-who-as-depression-tops-list-of-causes-of-ill-health |
| [2] NMHS, "No. 129" | C | The Summary is Publication **No. 128**. The treatment-gap figures now cite peer-reviewed NMHS papers: depression 79.1% and prevalence 2.68% (Arvind et al., BMJ Open 2019, doi:10.1136/bmjopen-2018-027250); overall 84.5% (Gautham et al., IJSP 2020, doi:10.1177/0020764020907941). The old "75%–85%" range was not a figure the survey reports. |
| "≈0.75 per 100,000" | V | These are **psychiatrists** (the old text said "practitioners"). Garg, Kumar, Chandra, Indian J Psychiatry 2019, doi:10.4103/psychiatry.IndianJPsychiatry_7_18. |
| [3] Kessler 2003 | V | doi:10.1001/archpsyc.60.2.184 |
| [4] Kroenke 2001 | V | doi:10.1046/j.1525-1497.2001.016009606.x. Thresholds 5/10/15/20. The "None–minimal" label comes from the PHQ-9 scoring sheet (BC Guidelines). |
| [5] MentalBERT | V | https://aclanthology.org/2022.lrec-1.778/ |
| [6] Mental-LLM "Proc. ACL 2024" | **C** | It is **Proc. ACM IMWUT**, vol. 8, no. 1, 2024, doi:10.1145/3643540. |
| [7] Cummins 2015 | V | doi:10.1016/j.specom.2015.03.004 |
| [8] Scherer 2013 | V | doi:10.1109/FG.2013.6553789 |
| [9] Yang, Jiang, Cambria, IEEE TAC 2023 | **R** | **No such paper was found**, so it was probably fabricated. Replaced with Mao et al., npj Mental Health Research 2023 (doi:10.1038/s44184-023-00040-z) and He et al., Information Fusion 2022 (doi:10.1016/j.inffus.2021.10.012). |
| [10] AVEC 2019 | V | doi:10.1145/3347320.3357688 |
| [11] "T. DeVault" | **C** | The first author is **D. DeVault**. https://www.ifaamas.org/Proceedings/aamas2014/aamas/p1061.pdf |
| [12] Woebot | V | Full title added; doi:10.2196/mental.7785 |
| [13] Hartmann model card | V | The model card asks users to cite the Hugging Face page. Its 7 labels, 6 training datasets and 66% accuracy are now stated. |
| [14] Guo 2017 | V | PMLR vol. 70, pp. 1321–1330 |
| [15] Tele-MANAS | V | Launched 10 Oct 2022; 14416 / 1-800-891-4416. Now cites the PIB explainer (13 Oct 2024). |
| [16] KIRAN | Removed | Reported as merged into Tele-MANAS (Digital Health News, Nov 2024). No official notice was found. |

**47 new references were added** (NegEx, ConText, Levis 2019 BMJ, Simon 2013, Louzon 2016, C-SSRS, Joint Commission SEA 56, NIMH ASQ, DAIC-WOZ, DepAudioNet, Al Hanai 2018, Low 2020, Mundt 2012, Cannizzaro 2004, Quatieri 2012, PHQ-8, Baltrušaitis 2019, SMIL, Huang 2018, Madruga 2023, Ji 2021, Bernert 2020, Shing 2018, CLPsych 2019, Gaur 2019, SDCNL, the Hinglish corpus, GLUECoS, Sutton 2020, NeMo Guardrails, Llama Guard, McBain 2025, Moore 2025, Hinton 2015, W3C Media Capture, W3C Web Audio, Gemini deprecations page, DPDP Act and Rules, and others).

Each one was checked on a publisher page, DOI record, ACL Anthology, ISCA archive, arXiv or an official page. Where only part of an author list could be confirmed, we used "et al." rather than guessing names.

Details we **could not** confirm are not stated in the paper:
- the DepAudioNet F1 scores;
- the He et al. 2022 volume and page numbers;
- current browser defaults for AGC.

---

## 6. Plagiarism (similarity) spot-check

This was a web search on 14 distinctive sentences from the old paper, not a full iThenticate scan.

- **Other authors' text:** no copied text found. The WHO, NMHS and "4-7-8 / 5-4-3-2-1" phrasing is common wording and is cited.
- **Your own earlier version:** the whole paper is public on GitHub (Section 1, item 1). This is the one real similarity risk.
- **The revised paper:** it was written fresh. Its wording is new, so it should not match the GitHub copy beyond short technical phrases, equations and reference entries.

---

## 7. Remaining honest limitations (already stated in the paper)

- There is no clinical validation, and the paper claims no diagnostic accuracy.
- The emotion-model branch and the audio branch were **not** validated against depression labels.
- The test corpora have noisy labels. SDCNL labels come from subreddit membership; the tweet corpus has undocumented provenance.
- The design-space analysis weights input configurations uniformly. It is not a population estimate.
- Two results were produced after the main evaluation, and the paper labels both as post hoc: the v2.1 self-harm change and the vocabulary ablation.
