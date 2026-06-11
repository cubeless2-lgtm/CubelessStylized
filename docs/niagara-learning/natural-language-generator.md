# Niagara Natural-Language Generator

This is the first safe generation layer built on top of the Niagara learning index.

The current tool does not edit original Niagara assets. It converts a natural-language request into:

- parsed intent: categories, color words, shape words, motion words, duration
- best source NiagaraSystem template
- supporting template candidates
- useful NiagaraEmitter and parameter collection candidates
- destination package under `/Game/_MCP_Temp/NiagaraGenerated`
- optional Unreal Python script that duplicates the chosen template into the destination

## Tool

`Tools/Unreal/niagara_natural_language_generator.py`

## Example

```powershell
& "C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  Tools\Unreal\niagara_natural_language_generator.py `
  "푸른 번개 장판, 2초 지속, 원형으로 퍼지고 위로 스파크가 튄다" `
  --output-name blue_lightning_field `
  --emit-unreal-python
```

If a terminal displays Korean text incorrectly, put the prompt in a UTF-8 text file and use `--prompt-file`:

```powershell
& "C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  Tools\Unreal\niagara_natural_language_generator.py `
  --prompt-file Saved\MCP_NiagaraGeneration\prompt.txt `
  --output-name blue_lightning_field `
  --emit-unreal-python
```

Expected outputs:

- `Saved/MCP_NiagaraGeneration/blue_lightning_field_plan.json`
- `Saved/MCP_NiagaraGeneration/blue_lightning_field_duplicate_unreal.py`

The generated Unreal Python script duplicates only the selected source NiagaraSystem. It writes the duplicate under:

`/Game/_MCP_Temp/NiagaraGenerated/blue_lightning_field/NG_blue_lightning_field`

## Current Capability

The generator can choose a template and produce a safe duplicate script. It can also recommend support templates, emitters, materials, textures, and parameter collections from the existing index.

## Current Limitation

Deep Niagara graph editing is intentionally not enabled yet. To turn this into full generation, the next layer should expose or implement stable UnrealMCP commands for:

- listing system emitters and exposed user parameters
- adding or removing emitters on a duplicate system
- setting exposed Niagara parameters
- validating compile status and log errors
- spawning a preview actor and capturing a screenshot

Until those commands exist, generated systems should be treated as template duplicates with a structured implementation plan.
