# 18A Stage 0

RESULT: BLOCKED

DEPLOYED_SEED_REPRODUCED: true
PARAM_COUNT: D16=1731 / G16=370 / G8=186
EXACTLY_ONE_VARIABLE_DIFFERS (D16 vs G16): yes (the preregistered 05f recurrence block)
EXACTLY_ONE_VARIABLE_DIFFERS (G16 vs G8): yes (hidden dimension)
PROTECTED_HASHES_UNCHANGED: true

EPOCH_SECONDS: D16=1760.921 / G16=11.993
WORST_CASE_ETA_PER_SEED_H: D16=244.572 / G16=1.666

The actual 11B code uses AdamW with weight_decay=1e-4 and gradient clipping=1.0. These are retained identically for all models.

D16 exceeds the preregistered 12-hour worst-case limit. Stopped before Stage 1.

Reviewer options (not executed):

1. Authorize the measured protocol unchanged at about 244.572 hours per D16 seed
   (about 733.717 hours for three seeds at the 500-epoch upper bound).
2. Define and preregister a computationally equivalent dense-transition
   implementation, then rerun the one-epoch timing gate before training.
3. Amend the protocol (epochs, chunks, batches, or optimizer). This would create
   a new experimental condition and would no longer satisfy the issued 18A spec.
4. Record D16 as computationally blocked under the current protocol and report
   G16/G8 capacity only in a separately authorized task.

No option above was selected automatically, and Stage 1/2 were not started.
