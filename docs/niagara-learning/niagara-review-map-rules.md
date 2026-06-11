# Niagara Review Map Rules

All Niagara generation, duplication, material replacement, Scratch Pad behavior testing, and final visual review must use the dedicated Niagara review map:

```text
/Script/Engine.World'/Game/SampleTestMap/Niagara_TestMap.Niagara_TestMap'
```

## Camera Bookmarks

Use the map's existing editor camera bookmarks:

| Bookmark | Review distance |
| --- | --- |
| 1 | Near |
| 2 | Mid |
| 3 | Far |

## Screenshot Rule

Every generated Niagara review report should include screenshots from all three bookmarks.

The report must call out failures such as:

- effect is not visible from one or more bookmarks
- effect is too small or too large for the review frame
- effect is off-center
- effect reads well near but not mid/far
- timing makes the effect miss the capture frame
- material is too dim, too bright, or visually inconsistent with the stylized reference

## Scope

This rule applies to:

- `_MCP_Temp` duplicate tests
- generated primitive tests
- generated material instance tests
- BP/User parameter integration tests
- Scratch Pad reuse or generation tests
- production promotion reviews

Original reference assets remain read-only during these reviews.
