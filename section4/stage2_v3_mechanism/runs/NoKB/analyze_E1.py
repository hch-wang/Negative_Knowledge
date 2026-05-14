"""Post-process E1: extract trajectories of diagnostics for both ICs and report
features that discriminate among H_A, H_B, H_C."""
import numpy as np
import os, json

R = {}
for tag in ("A_onmfd", "B_offmfd"):
    d = np.load(f"pred_results/E1_{tag}.npz")
    R[tag] = {k: d[k] for k in d.files}

x = R["A_onmfd"]["x"]
dx = x[1]-x[0]

def report(tag):
    r = R[tag]
    t = r["times"]
    print(f"\n========== {tag} ==========")
    print(f"  T range: {t[0]:.2f} -> {t[-1]:.2f},  Npts = {len(t)}")
    # m metrics over time
    m_l2 = r["m_l2"]; m_inf = r["m_inf"]
    print("  ||m||_L2  trajectory (every ~5pts):")
    for i in range(0, len(t), max(1,len(t)//8)):
        print(f"    t={t[i]:6.2f}  ||m||_L2={m_l2[i]:7.4f}  ||m||_inf={m_inf[i]:7.4f}  lock={r['lock'][i]:6.3f}")
    print(f"    t={t[-1]:6.2f}  ||m||_L2={m_l2[-1]:7.4f}  ||m||_inf={m_inf[-1]:7.4f}  lock={r['lock'][-1]:6.3f}")
    # spectra
    print("  energy partition u:")
    for i in [0, len(t)//4, len(t)//2, 3*len(t)//4, len(t)-1]:
        print(f"    t={t[i]:6.2f}  E_low_u={r['el_u'][i]:.4e}  E_high_u={r['eh_u'][i]:.4e}  ratio_high/total={r['eh_u'][i]/(r['el_u'][i]+r['eh_u'][i]+1e-20):.3e}")
    print("  energy partition v:")
    for i in [0, len(t)//4, len(t)//2, 3*len(t)//4, len(t)-1]:
        print(f"    t={t[i]:6.2f}  E_low_v={r['el_v'][i]:.4e}  E_high_v={r['eh_v'][i]:.4e}  ratio_high/total={r['eh_v'][i]/(r['el_v'][i]+r['eh_v'][i]+1e-20):.3e}")
    # peak amplitude and position of v
    snaps = r["snaps"]; snap_t = r["snap_times"]
    print("  v(x,t) peak amplitude & position over time:")
    for i in range(len(snap_t)):
        v = snaps[i,1]
        ip = np.argmax(v)
        u = snaps[i,0]
        iu = np.argmax(np.abs(u))
        print(f"    t={snap_t[i]:6.2f}  vmax={v[ip]:7.4f} at x={x[ip]:6.2f};   |u|max={np.abs(u[iu]):7.4f} at x={x[iu]:6.2f}")
    return r

rA = report("A_onmfd")
rB = report("B_offmfd")

# Key discriminations
print("\n==================== SUMMARY for hypothesis discrimination ====================")
print("H_A (Gardner-manifold attraction): would predict ||m|| to DECREASE for IC_B,")
print("    or at least for both ICs to converge to a common small ||m|| value.")
print(f"  ||m||_L2 final:  A={rA['m_l2'][-1]:.4f},  B={rB['m_l2'][-1]:.4f}")
print(f"  ||m||_L2 initial: A={rA['m_l2'][0]:.4f},  B={rB['m_l2'][0]:.4f}")
print(f"  ratio final/initial: A={rA['m_l2'][-1]/max(rA['m_l2'][0],1e-9):.2f},   B={rB['m_l2'][-1]/max(rB['m_l2'][0],1e-9):.2f}")

print("\nH_B (radiative cooling): would predict v's high-k energy to DECREASE over time.")
ratio_v_A = rA['eh_v'][-1]/max(rA['eh_v'][0],1e-12)
ratio_v_B = rB['eh_v'][-1]/max(rB['eh_v'][0],1e-12)
print(f"  E_high_v final/initial:  A={ratio_v_A:.4f},  B={ratio_v_B:.4f}")
print("  (note: u's high-k energy GROWS — that's Burgers-front steepening, not radiation)")

print("\nH_C (Hamiltonian / lock to v^2/2): would predict lock_corr -> 1 at late time.")
print(f"  lock_corr final: A={rA['lock'][-1]:.3f},  B={rB['lock'][-1]:.3f}")

# Save analysis output
with open("evidence/E1_analysis.txt", "w") as f:
    import io, sys
    # dump same info as text
    f.write(f"E1 analysis summary\n")
    f.write(f"========================\n")
    f.write(f"||m||_L2 final A={rA['m_l2'][-1]:.4f}  B={rB['m_l2'][-1]:.4f}\n")
    f.write(f"||m||_L2 init  A={rA['m_l2'][0]:.4f}  B={rB['m_l2'][0]:.4f}\n")
    f.write(f"lock_corr final A={rA['lock'][-1]:.3f}  B={rB['lock'][-1]:.3f}\n")
    f.write(f"lock_corr init  A={rA['lock'][0]:.3f}  B={rB['lock'][0]:.3f}\n")
    f.write(f"E_high_v final/init  A={ratio_v_A:.4f}  B={ratio_v_B:.4f}\n")
print("\nSaved evidence/E1_analysis.txt")
