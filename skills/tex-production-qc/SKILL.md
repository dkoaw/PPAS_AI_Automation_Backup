---
name: Tex Production QC
description: Dedicated skill for artist-side texture QC and architectural validation.
---
# Tex Production QC Skill

## Purpose
This skill handles the texture quality control flow for artists before they publish their assets. It operates on a separate spreadsheet to avoid permission conflicts with the master library.

## Components
- `manage_tex_spreadsheet.py`: Manages the `{Project}_Tex制作管理表.xlsx`.
- `tex_pipeline_executor.py`: Orchestrates the QC process (fixing, screening, atomic QC, architectural comparison).
- `stages/stage_tex_qc.py`: The core QC logic for the production environment.

## Workflow
1. Sync `texMaster` status from ShotGrid to the local Tex Management Spreadsheet.
2. Scan for assets where `texMaster == 'fin'` and `texQC != 'fin'`.
3. execute QC in a mirrored black-box workspace in `X:\AI_Automation\Project`.
4. Output passed files to the mirrored `texMaster` folder with clean naming.
5. Update the local Tex Management Spreadsheet with the results.
