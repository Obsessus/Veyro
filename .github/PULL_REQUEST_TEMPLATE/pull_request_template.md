## What does this PR do?
<!-- One paragraph. Clear and direct. -->

## Which phase does this belong to?
- [ ] Phase 1 — Core (activation / cursor / click)
- [ ] Phase 2 — Extensions (scroll / drag / tab switch)
- [ ] Phase 3 — Future
- [ ] Docs / tests / benchmarks / chore

## Checklist
- [ ] All thresholds are named constants in `config.py` — no magic numbers inline
- [ ] Gesture classifiers tested without a live camera (fixture-based tests pass)
- [ ] `gestures/`, `state_machine/`, and `actions/` layers remain strictly separate
- [ ] `pytest` passes locally
- [ ] No new pixel-space thresholds — gesture distances use 3D world landmarks
- [ ] Benchmark result included below (if performance-related)

## Benchmark result (if applicable)
<!-- Before / after FPS and latency. Run on your actual hardware. -->

## Screenshots / recordings (if applicable)
<!-- A short clip of the gesture working in --dev mode is worth a thousand words. -->

## Related issue
<!-- Closes #XXX -->
