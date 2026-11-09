"""
lenticule_compare.py — сравнение математических моделей лентикулы между глазами и сроками.

Вход: JSON-файлы parametry_*.json (выход lenticule_math_model.py) и описание наблюдений в CSV:
    kod;json;dT_csv;dney
    P01_OS;.../parametry_P01_OS.json;.../ubyl_tolshchiny_P01_OS_mkm.csv;1
Выход: сводная таблица (CSV, MD), рисунок «α и σ по срокам», профили «измерено / план» по плоскому и крутому меридианам.
"""
import argparse, csv, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lenticule_model import Lenticule
from lenticule_math_model import read_map, model_A


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--list', required=True); ap.add_argument('--out', default='out/lenticule_compare')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    rows = [r for r in csv.DictReader(open(A.list), delimiter=';')]
    data = []
    for r in rows:
        j = json.load(open(r['json'])); a, b = j['model_A'], j['model_B']
        data.append(dict(kod=r['kod'], dney=float(r['dney']), A=a, B=b, dT=r['dT_csv'], stroma=('stroma' in r['kod'])))

    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from lenticule_style import FLAT_COL, STEEP_COL, PLAN_COL, HALO
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    eyes = sorted({d['kod'].split('_')[0] + '_' + d['kod'].split('_')[1] for d in data})
    cols = dict(zip(eyes, ['#178a73', '#4f84b3', '#b0628c', '#d0613f', '#6b5ca5']))

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    for e in eyes:
        pts = sorted([d for d in data if d['kod'].startswith(e) and not d['stroma'] and d['B']], key=lambda d: d['dney'])
        st = [d for d in data if d['kod'].startswith(e) and d['stroma'] and d['B']]
        for ax, key in ((axs[0], 'alpha'), (axs[1], 'sigma_mm')):
            ax.plot([d['dney'] for d in pts], [d['B'][key] for d in pts], 'o-', color=cols[e], lw=2, ms=7, label=e)
            for d in st: ax.plot(d['dney'], d['B'][key], 'D', color=cols[e], mfc='white', mew=2, ms=8, label=f'{e}: строма (поправка на эпителий ОКТ)')
    for ax, ttl, yl in ((axs[0], 'α — доля плановой толщины лентикулы', 'α'), (axs[1], 'σ — размытие края лентикулы', 'σ, мм')):
        ax.set_xscale('log'); ax.set_xticks([1, 7, 24, 90, 230]); ax.set_xticklabels(['1 сут', '1 нед', '24 дн', '3 мес', '7,5 мес'])
        ax.set_title(ttl); ax.set_ylabel(yl); ax.set_xlabel('срок после операции'); ax.grid(alpha=0.3)
    axs[0].axhline(1, color=PLAN_COL, ls='--', lw=1); axs[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, 'alfa_sigma_po_srokam.png'), dpi=160); plt.close(fig)

    # профили «измерено / план» на последнем сроке каждого глаза (по возможности — строма)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for e in eyes:
        cand = [d for d in data if d['kod'].startswith(e) and d['B']]
        last = max(cand, key=lambda d: (d['dney'], d['stroma']))
        xs, ys, Z = read_map(last['dT']); pl = last['B']['plan']
        Lp = Lenticule(pl['sph_cornea'], pl['cyl_cornea'], pl['axis'], pl['oz'], pl['tmin'])
        from scipy.interpolate import RegularGridInterpolator
        I = RegularGridInterpolator((ys[::-1], xs), Z[::-1], bounds_error=False, fill_value=np.nan)
        rs = np.linspace(-4, 4, 161)
        for ax, ang in ((axs[0], pl['axis']), (axs[1], pl['axis'] + 90)):
            a = math.radians(ang); q = np.stack([rs * math.sin(a), rs * math.cos(a)], -1)
            ax.plot(rs, I(q), color=cols[e], lw=2.2, label=f"{last['kod']} (измерено)")
            ax.plot(rs, np.nan_to_num(Lp.thickness(rs * math.cos(a), rs * math.sin(a)), nan=0), color=cols[e], lw=1.3, ls='--', label=f'{e}: план')
    axs[0].set_title('Плоский меридиан (ось цилиндра плана)'); axs[1].set_title('Крутой меридиан (ось + 90°)')
    for ax in axs: ax.set_xlabel('расстояние от центра, мм'); ax.grid(alpha=0.3)
    axs[0].set_ylabel('толщина лентикулы, мкм'); axs[0].legend(fontsize=7.5); axs[0].set_ylim(0, None)
    fig.tight_layout(); fig.savefig(os.path.join(A.out, 'profili_plan_izmereno.png'), dpi=160); plt.close(fig)

    # таблица
    hdr = ['kod', 'dney', 't0_um', 'theta0_deg', 'P_flat_D', 'P_steep_D', 'R_flat_mm', 'R_steep_mm', 'w_mm', 'rmsA_um', 'alpha', 'sigma_mm', 'rmsB_um',
           'plan_P_flat_D', 'plan_P_steep_D', 'plan_t0_um']
    with open(os.path.join(A.out, 'svodka_modelej.csv'), 'w') as f:
        w = csv.writer(f, delimiter=';'); w.writerow(hdr)
        for d in data:
            a, b = d['A'], d['B'] or {}
            pl = b.get('plan', {})
            w.writerow([d['kod'], d['dney'], f"{a['t0_um']:.1f}", f"{a['theta0_deg']:.0f}", f"{a['P_along_theta0_D']:.2f}", f"{a['P_along_theta0_plus90_D']:.2f}",
                        f"{a['R_edge_theta0_mm']:.2f}", f"{a['R_edge_theta0_plus90_mm']:.2f}", f"{a['edge_width_mm']:.2f}", f"{a['rms_um']:.1f}",
                        f"{b.get('alpha', float('nan')):.2f}", f"{b.get('sigma_mm', float('nan')):.2f}", f"{b.get('rms_um', float('nan')):.1f}",
                        f"{pl.get('sph_cornea', float('nan')):.2f}", f"{pl.get('sph_cornea', 0) + pl.get('cyl_cornea', 0):.2f}", f"{pl.get('t0', float('nan')):.0f}"])
    print(open(os.path.join(A.out, 'svodka_modelej.csv')).read())


if __name__ == '__main__':
    main()
