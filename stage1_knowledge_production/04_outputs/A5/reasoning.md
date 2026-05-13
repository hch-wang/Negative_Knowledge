# Reasoning: KdV Stress Test A5

## Method as written

Fourier pseudo-spectral spatial discretization on a periodic domain with IMEX Euler time integration (dt = 0.005): the dispersive term v_xxx is treated implicitly (exact in Fourier space) and the nonlinear term -6 v v_x is treated explicitly, with absolutely no 2/3 dealiasing rule, no low-pass filtering, and no mode truncation applied to the nonlinear term.

## Predicted vs expected

I agree with the predicted outcome. Without dealiasing, the pseudo-spectral evaluation of v v_x folds energy from modes k and k' (with |k| + |k'| > N/2) back into low wavenumbers. For the KdV soliton, which concentrates energy at low k but generates harmonics through nonlinearity, this aliasing error accumulates over time. Expected symptoms: spurious high-wavenumber oscillations growing on the trailing edge of the soliton, slight distortion of the soliton peak speed/shape (since aliased energy acts as a phantom forcing), and a slow drift in the L2 norm or mass because energy is misattributed across modes.

## What knowledge this might produce

A future agent learning from this run can quantify the aliasing-induced error for KdV at Nx=256 without dealiasing — specifically how much the soliton peak amplitude and position deviate from the reference 2/3-dealiased solution at T=2.0. This provides a concrete cost/benefit data point: dealiasing adds ~50% more FFT work but eliminates an O(dt * aliasing_energy) error per step that compounds over hundreds of steps.
