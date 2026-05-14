# Session log: T_B / NoKB

iter 1: E1 (Fourier pseudospectral, no dealiasing, RK4, dt=5e-5) blew up at t=0.28 from aliasing cascade in v^2 / (u v) products feeding v_xxx-amplified high-k modes.
iter 2: E2 added 2/3-rule dealiasing on every nonlinear product; survived until t~3.0 then u-channel ran away to |u|~1170 from inviscid Burgers shock formation (off-manifold u(x,0)=0 IC drives 3 u u_x to steepen without dissipation). Mass(v) stayed perfectly conserved throughout.
iter 3: E3 added small k^8 spectral hyperviscosity (eps chosen so dissipation rate at the 2/3-dealias cutoff is ~10 s^-1, leaving soliton-scale k~4 essentially untouched). Run completed to T=6.0, max|v|=4.37, max|u|=49.3, mass(v) drift 0.000%. Final v has 6 well-separated peak clusters (separation > 1.5), each cluster-peak amplitude in [2.4, 4.4] — satisfies the phenomenon target.
