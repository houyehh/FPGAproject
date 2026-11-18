# 07P Stage 1: Scalar-Port PHC Pipeline Sweep

status: `completed_no_deployable_point`

## Scope and interface

Stage 1 copied the frozen 06U V3 diagonal source and weights into 07P. No file under `06u_phc_latency_breakthrough/` was modified, and the copied weight header retains SHA-256 `60C29F2C4898AE4747E563648EB37E2C198027AAEB1AC13C9990960DF616CA5A` for every variant.

The memory-style input ports were replaced by 32 independent `ap_fixed<24,12>` scalar arguments. The 18 scalar results are bit-packed into one `ap_uint<432>` scalar output (`2 * 24` readout bits followed by `16 * 24` state bits). This is a scalar `ap_none` RTL port, not an array memory interface; it avoids address/CE serialization while keeping the top-level argument count manageable. The arithmetic expressions, weights, and fixed-point formats remain unchanged. The top uses `ap_ctrl_hs` and `#pragma HLS PIPELINE II=1`.

## Sweep result

| Requested unroll | CSim | csynth latency / II | DSP | LUT | FF | BRAM_18K | RTL cosim | Tier |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 2 | 25,600 / 0 mismatch | 146 / 1 | 781 (355.00%) | 106,041 (199.33%) | 115,774 (108.81%) | 0 (0.00%) | PASS, 1,000 / 0 mismatch, 146 cycles, II=1 | `timing_only_not_deployable` |
| 4 | 25,600 / 0 mismatch | 146 / 1 | 781 (355.00%) | 106,041 (199.33%) | 115,774 (108.81%) | 0 (0.00%) | not run: identical csynth and already over budget | `timing_only_not_deployable` |
| 8 | 25,600 / 0 mismatch | 146 / 1 | 781 (355.00%) | 106,041 (199.33%) | 115,774 (108.81%) | 0 (0.00%) | not run: identical csynth and already over budget | `timing_only_not_deployable` |
| 16 | 25,600 / 0 mismatch | 146 / 1 | 781 (355.00%) | 106,041 (199.33%) | 115,774 (108.81%) | 0 (0.00%) | not run: identical csynth and already over budget | `timing_only_not_deployable` |

The four csynth XML reports are byte-identical. Vitis emits `HLS 214-275` for each partially unrolled loop: a loop inside the top pipelined region is converted to complete unroll. Consequently, the requested factors do not create four hardware trade-off points; they collapse to one fully unrolled implementation.

At the 100 MHz target, the csynth-estimated latency is 1.460 us. Relative to the 530-cycle reference this is a 3.63x cycle reduction. For recurrent event processing, the state dependency limits the event rate to `100,000,000 / 146 = 684,932 events/s`; the reported core II of 1 does not imply a 100 million event/s recurrent system rate.

The implementation exceeds all three relevant fabric budgets: DSP by 3.55x, LUT by 1.99x, and FF by 1.09x. It was therefore not routed. `routed WNS` is `not_measured`, no row is deployable, and the Stage 1 lower bound must not be described as a routed or on-board result.

## Required endpoint comparison

| Core | Latency | Core II | Recurrent max event rate | DSP | BRAM | Verification |
|---|---:|---:|---:|---:|---:|---|
| PHC V3 deployed reference | 530 cycles / 5,300 ns | not used as system rate | 188,324/s (reported reference) | 196 (89.09%) | 0 | cosim + routed |
| 07P fully pipelined PHC | 146 cycles / 1,460 ns | 1 | 684,932/s (`100 MHz / 146`) | 781 (355.00%) | 0 | representative cosim; not routable on Zynq-7020 |
| Tiny MLP 07M | 8 cycles / 80 ns | 1 | 100,000,000/s | 36 (16.36%) | 0 | cosim + routed |

The Tiny MLP rate is possible because it has no recurrent state dependency. The PHC system cannot accept the next event merely because the internal pipeline reports II=1: event `t+1` requires the completed state from event `t`, so its system event rate remains latency-limited. The Tiny MLP and PHC rates are therefore structural endpoints, not interchangeable interpretations of II.

## Pipeline equivalence result

The unroll-2 representative, whose synthesized schedule and resources are identical to the other factors, passed RTL cosimulation on 1,000 vectors with zero mismatches. The cosim report gives latency min/avg/max `146/146/146` and interval `1/1/1`. This refutes the broad hypothesis that an active top-level pipeline necessarily breaks C/RTL equivalence for this core. It does not retroactively explain the older non-local-partition failures, because Stage 1 also changes the top-level interface and retains local partitioning.

## Cycle attribution

Vitis inlined all helper functions into one pipelined schedule, so the following values are schedule occupancy spans and are deliberately **not additive**. Overlap is expected.

| Region | First-last schedule state | Occupancy span | Share of 146-cycle latency |
|---|---:|---:|---:|
| encoder stage, total | 1-129 | 129 | 88.36% |
| encoder dense substage | 1-11 | 11 | 7.53% |
| `layernorm_16` | 10-121 | 112 | 76.71% |
| `silu_16` | 121-129 | 9 | 6.16% |
| recurrence stage | 129-145 | 17 | 11.64% |
| readout stage | 131-147 | 17 | 11.64% |

`layernorm_16` spans 76.71% of the latency, above the predeclared 50% threshold. It is therefore the numerical block worth investigating next. The encoder dense operation is no longer the latency bottleneck after complete unrolling; it is the main reason for the resource explosion.

## Evidence paths

- Machine-readable sweep: `results/stage1_summary.csv`
- Machine-readable attribution: `results/stage1_cycle_attribution.csv`
- Per-factor csynth reports: `stage1_variants/unroll*/hls_component/hls_component/hls/syn/report/phc_diag_step_scalar_pipeline_csynth.rpt`
- Representative cosim report: `stage1_variants/unroll2/hls_component/hls_component/hls/sim/report/phc_diag_step_scalar_pipeline_cosim.rpt`
- Vitis complete-unroll diagnostics: `stage1_variants/unroll*/hls_component/hls_component/hls/hls.log`
- Full schedule evidence: `stage1_variants/unroll*/hls_component/hls_component/hls/.autopilot/db/phc_diag_step_scalar_pipeline.verbose.sched.rpt`

## Stage decision

- Latency lower bound under the unchanged arithmetic: **146 cycles / 1.460 us at 100 MHz**, `timing_only_not_deployable`.
- Best budget-compliant deployable point from this Stage 1 sweep: **none**.
- LayerNorm decision: proceed to a separately reviewed Stage 2 numerical investigation; do not continue automatically.
