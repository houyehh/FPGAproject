# AUDIT 15A

- Data: FI-2010 Setup 2 cache used by 09J (`train_cf7`, `test_cf7`, `test_cf8`, `test_cf9`).
- Horizon: k=50.
- Loss: raw cross entropy.
- Optimizer: Adam, lr=1e-3, weight decay=0, no scheduler.
- Early stopping: patience 10; max epoch safety limit 120.
- Seeds: 0, 1, 2.
- Training implementation: original 09J `03_run_track_b.py:train_one`.
- Feedforward side: not retrained; existing complete 09J artifacts used for paired tests.
- Numeric stop epochs: yes, 6/6.
- Natural early stops: yes, 6/6.
- Required artifacts complete: true (18/18).
- NEW5 used: no.
