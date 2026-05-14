"""
E3: layer ONE more component on E2.

Change versus E2: add 2/3-rule dealiasing on the FFT of every nonlinear product
(u*u_x, v^2, u*v, v*v_x). The dispersive linear coupling (CN) and pseudospectral
derivatives are unchanged. dt is also reduced to 1e-4 to satisfy the nonlinear
CFL at amplitude 4 implied by kb-gardner-nonlinearCFL-amplitude-boundary
(max|6A + 1.5A^2| at A=4 is 24+24=48; at A=1.5 is ~12.4; ratio ~3.9, so dt budget
~5e-4/3.9~1.3e-4 -> pick 1e-4).

PDE (in flux form):
  u_t = -3 u u_x - 3 (v^2)_x - v_xxx
  v_t = -6 v v_x - v_xxx       - (u v)_x

Linear stiff L (in Fourier): both L_u and L_v = +i k^3 v_hat.

Update (in Fourier, IMEX-CN):
  v_hat^{n+1} = [(1 + 0.5 dt i k^3) v_hat^n + dt N_v_hat^n] / (1 - 0.5 dt i k^3)
  u_hat^{n+1} =  u_hat^n + 0.5 dt i k^3 (v_hat^{n+1} + v_hat^n) + dt N_u_hat^n

with all nonlinear-product FFTs masked by the 2/3 dealiasing filter.

Bank justification:
  Positive: kb-kdv-IMEX-CN-spectral-pass (KdV amp 2 dt 5e-4 with 2/3 dealiasing works);
            kb-gardner-G2-IMEX-CN-dealiased-stableRadiation (Gardner amp 1.5 dt 5e-4 with 2/3 dealiasing works);
            kb-kdv-spectral-solitonAmplitude-conservation (spectral IMEX preserves
            soliton amplitude/mass within ~2%).
  Negative: kb-kdv-noDealiasing-aliasing-artifacts (no dealiasing inflates amp 43%,
            creates 4 spurious peaks); kb-gardner-G3-noDealiasing-cubicAliasing
            (Gardner without dealiasing makes 11 spurious peaks); kb-gardner-G4
            (amp 3, dt 1e-4 blew up even with IMEX -> amp 4 needs smaller dt or stronger
            filter).
"""

import os
import numpy as np

os.makedirs("pred_results", exist_ok=True)

# --- Domain ---
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
ik = 1j * k
k3 = k ** 3

# --- 2/3 dealiasing mask ---
k_max = np.max(np.abs(k))
cutoff = (2.0 / 3.0) * k_max
mask = (np.abs(k) <= cutoff).astype(float)

# --- IC ---
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros_like(x)

# --- Time stepping ---
T = 6.0
# Empirically: dt=2e-5 reached t=3.72 then NaN'd; dt=1e-4 NaN'd at t=1.2; dt=5e-4 NaN'd
# at t=0.5. Same-method bug-fix re-tune: drop dt by 2x more to 1e-5. Per progressive-
# complexity discipline, reducing dt is the single allowed parameter axis here.
dt = 1.0e-5
n_steps = int(round(T / dt))

# --- Snapshots ---
n_snapshots = 13
snapshot_steps = np.linspace(0, n_steps, n_snapshots).astype(int)
snapshot_set = set(int(s) for s in snapshot_steps)

# --- CN factors (in Fourier space) ---
half_dt_ik3 = 0.5 * dt * 1j * k3
denom = 1.0 - half_dt_ik3
numer_factor = 1.0 + half_dt_ik3  # multiplies v_hat^n


def nonlin_fft(u_hat, v_hat):
    """Compute the dealiased FFT of the nonlinear terms N_u, N_v."""
    # Dealias the input fields BEFORE forming products
    u_hat_d = u_hat * mask
    v_hat_d = v_hat * mask
    u = np.real(np.fft.ifft(u_hat_d))
    v = np.real(np.fft.ifft(v_hat_d))
    u_x = np.real(np.fft.ifft(ik * u_hat_d))
    v_x = np.real(np.fft.ifft(ik * v_hat_d))
    # Pointwise products (in real space)
    uux = u * u_x
    vvx = v * v_x
    v2 = v * v
    uv = u * v
    # Their FFTs, again masked (post-product dealiasing)
    uux_hat = np.fft.fft(uux) * mask
    vvx_hat = np.fft.fft(vvx) * mask
    v2_x_hat = ik * (np.fft.fft(v2) * mask)
    uv_x_hat = ik * (np.fft.fft(uv) * mask)
    # N_u_hat = -3 (u u_x)_hat - 3 (v^2)_x_hat
    N_u_hat = -3.0 * uux_hat - 3.0 * v2_x_hat
    # N_v_hat = -6 (v v_x)_hat - (u v)_x_hat
    N_v_hat = -6.0 * vvx_hat - uv_x_hat
    return N_u_hat, N_v_hat


u = u0.copy()
v = v0.copy()
u_hat = np.fft.fft(u) * mask
v_hat = np.fft.fft(v) * mask

snapshots = []
if 0 in snapshot_set:
    snapshots.append(np.stack([u.copy(), v.copy()]))

blow_up_step = None
for step in range(1, n_steps + 1):
    N_u_hat, N_v_hat = nonlin_fft(u_hat, v_hat)
    v_hat_new = (numer_factor * v_hat + dt * N_v_hat) / denom
    u_hat_new = u_hat + 0.5 * dt * 1j * k3 * (v_hat_new + v_hat) + dt * N_u_hat
    u_hat, v_hat = u_hat_new, v_hat_new
    # Optional: re-mask after step to avoid drift outside 2/3 set
    u_hat *= mask
    v_hat *= mask

    if step in snapshot_set:
        u = np.real(np.fft.ifft(u_hat))
        v = np.real(np.fft.ifft(v_hat))
        snapshots.append(np.stack([u.copy(), v.copy()]))

    if step % 2000 == 0:
        u_tmp = np.real(np.fft.ifft(u_hat))
        v_tmp = np.real(np.fft.ifft(v_hat))
        if not (np.isfinite(u_tmp).all() and np.isfinite(v_tmp).all()):
            blow_up_step = step
            print(f"NaN/Inf detected at step {step} (t={step*dt:.4f}); aborting.")
            break

u = np.real(np.fft.ifft(u_hat))
v = np.real(np.fft.ifft(v_hat))

while len(snapshots) < n_snapshots:
    snapshots.append(np.stack([u.copy(), v.copy()]))

out = np.stack(snapshots, axis=0)


def integ(f):
    return np.sum(f) * dx


print("Output shape:", out.shape)
print("Final |v|_max:", np.nanmax(np.abs(v)))
print("Final mass(v):", integ(v))
print("Initial mass(v):", integ(v0))
print("Mass drift fraction:", (integ(v) - integ(v0)) / integ(v0))
print("Final |u|_max:", np.nanmax(np.abs(u)))
print("All finite:", np.isfinite(out).all())
print("Blow-up step:", blow_up_step)


def local_maxima(arr, thresh=0.1):
    maxima = []
    for i in range(Nx):
        ip = (i + 1) % Nx
        im = (i - 1) % Nx
        if arr[i] > arr[ip] and arr[i] > arr[im] and arr[i] > thresh:
            maxima.append((i, arr[i]))
    return maxima


peaks_05 = local_maxima(v, thresh=0.5)
peaks_08 = local_maxima(v, thresh=0.8)
print(f"Number of v peaks above 0.5: {len(peaks_05)}")
print(f"Number of v peaks above 0.8: {len(peaks_08)}")
for ix, amp in peaks_05[:20]:
    print(f"  peak at x={x[ix]:+.3f} amp={amp:.4f}")

np.save("pred_results/T_B.npy", out)
print("Saved pred_results/T_B.npy")
