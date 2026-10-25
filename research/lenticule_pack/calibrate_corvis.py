"""
calibrate_corvis.py — Задача 2: подбор жёсткости роговицы по Corvis ST (SP-A1 до операции) и анализ чувствительности.

ВАЖНО (честно):
  * SP-A1 — динамический показатель (давление струи в момент 1-й аппланации минус bIOP, делённое на смещение вершины),
    а модель — квазистатическая. Поэтому сравнивается СУРРОГАТ: S = Δp / Δz_вершины при квазистатической «струе»
    p(r) = p0·exp(−r²/2σ²) на передней поверхности уже нагруженной ВГД роговицы (σ = 1,5 мм, p0 = 10 мм рт. ст. — допущения).
    Соответствие S ↔ SP-A1 принимается как S = κ·SP-A1 (κ = 1 по умолчанию). Это НЕ откалиброванная связь: для настоящей
    калибровки κ (и формы струи) нужны пары «Corvis + независимое измерение жёсткости» или динамическая модель.
  * Поэтому подобранный E — «эффективный модуль модели», а не измеренная жёсткость ткани; выводы — гипотезы.
  * Данные пациентов в код не записываются: файл глаз передаётся параметром --eyes (только коды глаз, без имён).
    В examples/corvis_demo_eyes.csv — ДЕМОНСТРАЦИОННЫЕ (выдуманные, типичные по литературе) значения, не пациенты.

Формат CSV (разделитель «;»):
    code;cct_um;iop_mmHg;r_ant_mm;sp_a1;sph;cyl;axis;oz;tmin
Запуск:
    python3 calibrate_corvis.py --eyes examples/corvis_demo_eyes.csv --out out/corvis
    python3 calibrate_corvis.py --sensitivity-only --out out/corvis
"""
from __future__ import annotations
import argparse, os, sys, csv, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem_hyper as H
import fem_lenticule as F
from lenticule_model import Lenticule

NU = 0.45
PUFF = dict(peak_mmHg=10.0, sigma_mm=1.5)


def cornea(cct_um=540, iop=15.0, r_ant=7.8, E=1.0, trans=0.5):
    cct = cct_um / 1000.0
    return F.Cornea(r_ant=r_ant, cct=cct, t_per=cct + 0.16, E=E, nu=NU, iop=iop, trans=trans)


def S_pre(C, L, nxy, nz):
    """Только «до»: ненапряжённая форма → ВГД → струя. Возвращает S (мм рт. ст./мм)."""
    gm = H.build_geo(C, L, False, nxy, nz)
    mat = H.Material.from_E_nu(C.E, NU)
    X0, pr, u, _ = H.stress_free(gm, mat, C, verbose=False)
    return H.puff_stiffness(pr, u, C, **PUFF)


def calibrate(C0, L, target, nxy, nz, tol=0.01, kappa=1.0, log=print):
    """Подбор E (МПа) так, чтобы S_модели = κ·SP-A1. Метод секущих по log E (S почти пропорционален E)."""
    target = kappa * target
    E = [0.5, 1.0]; S = []
    for e in E:
        C0.E = e; S.append(S_pre(C0, L, nxy, nz)); log(f'    E = {e:.4f} МПа → S = {S[-1]:.1f}')
    for it in range(8):
        la, lb = np.log(E[-2]), np.log(E[-1]); fa, fb = np.log(S[-2] / target), np.log(S[-1] / target)
        e = float(np.exp(lb - fb * (lb - la) / (fb - fa)))
        e = float(np.clip(e, 0.02, 20.0))
        C0.E = e; s = S_pre(C0, L, nxy, nz); E.append(e); S.append(s)
        log(f'    E = {e:.4f} МПа → S = {s:.1f} (цель {target:.1f})')
        if abs(s / target - 1) < tol:
            return e, s, list(zip(E, S))
    raise RuntimeError('калибровка не сошлась')


def read_eyes(path):
    with open(path, encoding='utf-8-sig') as f:
        rows = [r for r in csv.DictReader((l for l in f if not l.startswith('#')), delimiter=';')]
    return [{k: (v if k == 'code' else float(v)) for k, v in r.items()} for r in rows]


def run_eye(e, nxy, nz, kappa, log=print, nxy_cal=8, nz_cal=2):
    L = Lenticule(e['sph'], e['cyl'], e['axis'], e['oz'], e['tmin'])
    C = cornea(e['cct_um'], e['iop_mmHg'], e['r_ant_mm'])
    log(f'глаз {e["code"]}: SP-A1 {e["sp_a1"]:.0f}, CCT {e["cct_um"]:.0f} мкм, ВГД {e["iop_mmHg"]:.0f}, R {e["r_ant_mm"]}, '
        f'лентикула Sph {L.sph:+.2f} Cyl {L.cyl:+.2f} ось {L.axis:.0f}')
    E, S, hist = calibrate(C, L, e['sp_a1'], nxy_cal, nz_cal, kappa=kappa, log=log)   # подбор — на грубой сетке (быстро)
    C.E = E
    r = H.run_case(C, L, H.Material.from_E_nu(E, NU), nxy, nz, prestress=True, puff=PUFF); r.pop('_fields')
    out = dict(code=e['code'], sp_a1=e['sp_a1'], E_MPa=E, S_cal_coarse=S, S_pre=r['S_pre'], S_post=r['S_post'],
               S_change_pct=(r['S_post'] / r['S_pre'] - 1) * 100, apex_shift_um=r['apex_shift_um'],
               apex_iop_disp_pre_um=r['apex_iop_disp_pre_um'], apex_iop_disp_post_um=r['apex_iop_disp_post_um'],
               power_flat_D=L.sph, power_steep_D=L.sph + L.cyl,
               dK_flat=r['dK_flat'], dK_steep=r['dK_steep'], Kgeo_flat=r['Kgeo_flat'], Kgeo_steep=r['Kgeo_steep'],
               vm_pre_kPa=r['vm_pre_kPa'], vm_post_kPa=r['vm_post_kPa'], vm_change_pct=(r['vm_post_kPa'] / r['vm_pre_kPa'] - 1) * 100)
    log(f'  → E = {E:.3f} МПа; ΔK плоск {out["dK_flat"]:+.2f} (геом. {out["Kgeo_flat"]:+.2f}), ΔK крут {out["dK_steep"]:+.2f} '
        f'(геом. {out["Kgeo_steep"]:+.2f}); S {out["S_pre"]:.0f} → {out["S_post"]:.0f} ({out["S_change_pct"]:+.1f} %); '
        f'σ {out["vm_pre_kPa"]:.1f} → {out["vm_post_kPa"]:.1f} кПа')
    return out


# ------------------------------------------------------------------------------------------- чувствительность
BASE = dict(E=1.0, cct_um=540.0, iop=15.0, r_ant=7.8, trans=0.5)
VARY = [('E', 'модуль E, МПа', 0.5, 2.0), ('cct_um', 'центральная толщина, мкм', 500.0, 580.0),
        ('iop', 'ВГД, мм рт. ст.', 10.0, 20.0), ('r_ant', 'радиус передней поверхности, мм', 7.4, 8.2),
        ('trans', 'ширина переходной зоны, мм', 0.25, 1.0)]
OUTS = [('dK_steep', 'ΔK крутой меридиан, дптр'), ('dK_flat', 'ΔK плоский меридиан, дптр'),
        ('S_change_pct', 'изменение жёсткости S, %'), ('vm_change_pct', 'рост напряжения в зоне, %'), ('apex_shift_um', 'сдвиг вершины, мкм')]


def sens_case(p, L, nxy, nz):
    C = cornea(p['cct_um'], p['iop'], p['r_ant'], p['E'], p['trans'])
    r = H.run_case(C, L, H.Material.from_E_nu(p['E'], NU), nxy, nz, prestress=True, puff=PUFF); r.pop('_fields')
    r['S_change_pct'] = (r['S_post'] / r['S_pre'] - 1) * 100; r['vm_change_pct'] = (r['vm_post_kPa'] / r['vm_pre_kPa'] - 1) * 100
    return r


def sensitivity(L, nxy, nz, out, log=print):
    rows = []
    base = sens_case(BASE, L, nxy, nz); rows.append(dict(param='база', value='', **{k: base[k] for k, _ in OUTS}, S_pre=base['S_pre']))
    log('база: ' + ', '.join(f'{k} {base[k]:+.3f}' for k, _ in OUTS))
    for key, name, lo, hi in VARY:
        for v in (lo, hi):
            p = dict(BASE); p[key] = v
            r = sens_case(p, L, nxy, nz)
            rows.append(dict(param=name, value=v, **{k: r[k] for k, _ in OUTS}, S_pre=r['S_pre']))
            log(f'{name} = {v}: ' + ', '.join(f'{k} {r[k]:+.3f}' for k, _ in OUTS) + f', S_до {r["S_pre"]:.0f}')
    with open(f'{out}/sensitivity.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=';'); w.writeheader(); [w.writerow(r) for r in rows]
    # торнадо-диаграмма
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, len(OUTS), figsize=(4.2 * len(OUTS), 4.2), sharey=True)
    names = [v[1] for v in VARY]
    for ax, (k, title) in zip(axs, OUTS):
        b0 = base[k]
        for i, (key, name, lo, hi) in enumerate(VARY):
            rl = next(r for r in rows if r['param'] == name and r['value'] == lo)[k]
            rh = next(r for r in rows if r['param'] == name and r['value'] == hi)[k]
            ax.barh(i, rl - b0, left=b0, color='#6aa6e6', height=0.6); ax.barh(i, rh - b0, left=b0, color='#e4774a', height=0.6)
            ax.text(min(rl, rh), i, f'{lo:g}/{hi:g} ', va='center', ha='right', fontsize=7, color='#444') if False else None
        ax.axvline(b0, color='k', lw=0.8); ax.set_title(title, fontsize=9); ax.tick_params(labelsize=8)
    axs[0].set_yticks(range(len(VARY))); axs[0].set_yticklabels([f'{n}\n({lo:g} / {hi:g})' for _, n, lo, hi in VARY], fontsize=8)
    fig.suptitle('Чувствительность (нео-Гук, преднапряжение ВГД; синий — меньшее значение, оранжевый — большее). '
                 'Модельная гипотеза, не клинический результат', fontsize=9)
    fig.tight_layout(); fig.savefig(f'{out}/sensitivity.png', dpi=150)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--eyes', default=None); ap.add_argument('--kappa', type=float, default=1.0)
    ap.add_argument('--nxy', type=int, default=12); ap.add_argument('--nz', type=int, default=3)
    ap.add_argument('--nxy-cal', type=int, default=8); ap.add_argument('--nz-cal', type=int, default=2)
    ap.add_argument('--nxy-sens', type=int, default=8); ap.add_argument('--nz-sens', type=int, default=2)
    ap.add_argument('--sens-sph', type=float, default=1.0); ap.add_argument('--sens-cyl', type=float, default=-4.0); ap.add_argument('--sens-axis', type=float, default=0.0)
    ap.add_argument('--sensitivity-only', action='store_true'); ap.add_argument('--skip-sensitivity', action='store_true')
    ap.add_argument('--out', default='out/corvis')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    logf = open(f'{A.out}/log.txt', 'a', encoding='utf-8')
    def log(s): print(s, flush=True); logf.write(s + '\n'); logf.flush()
    t0 = time.time()
    if not A.sensitivity_only and A.eyes:
        res = [run_eye(e, A.nxy, A.nz, A.kappa, log, A.nxy_cal, A.nz_cal) for e in read_eyes(A.eyes)]
        with open(f'{A.out}/calibration.csv', 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(res[0].keys()), delimiter=';'); w.writeheader(); [w.writerow(r) for r in res]
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
        codes = [r['code'] for r in res]; x = np.arange(len(res))
        axs[0].scatter([r['sp_a1'] for r in res], [r['E_MPa'] for r in res], color='#2f6db3')
        for r in res: axs[0].annotate(r['code'], (r['sp_a1'], r['E_MPa']), fontsize=8, xytext=(3, 3), textcoords='offset points')
        axs[0].set_xlabel('SP-A1, мм рт. ст./мм'); axs[0].set_ylabel('подобранный E модели, МПа'); axs[0].set_title('Калибровка по SP-A1 (суррогат)')
        w_ = 0.38
        axs[1].bar(x - w_ / 2, [r['dK_steep'] / r['power_steep_D'] if r['power_steep_D'] else np.nan for r in res], w_, label='крутой', color='#e4774a')
        axs[1].bar(x + w_ / 2, [r['dK_flat'] / r['power_flat_D'] if r['power_flat_D'] else np.nan for r in res], w_, label='плоский', color='#6aa6e6')
        axs[1].axhline(0.8975, color='k', ls='--', lw=0.8, label='оптика 0,8975'); axs[1].set_xticks(x); axs[1].set_xticklabels(codes)
        axs[1].set_title('ΔK / сила меридиана (с ВГД)'); axs[1].legend(fontsize=8)
        axs[2].bar(x - w_ / 2, [r['S_change_pct'] for r in res], w_, label='жёсткость S, %', color='#2f6db3')
        axs[2].bar(x + w_ / 2, [r['vm_change_pct'] for r in res], w_, label='напряжение в зоне, %', color='#c4473a')
        axs[2].axhline(0, color='k', lw=0.6); axs[2].set_xticks(x); axs[2].set_xticklabels(codes); axs[2].legend(fontsize=8); axs[2].set_title('После операции относительно «до»')
        fig.suptitle('ДЕМО-глаза (не пациенты). Нео-Гук + преднапряжение ВГД; S — квазистатический суррогат SP-A1', fontsize=10)
        fig.tight_layout(); fig.savefig(f'{A.out}/calibration.png', dpi=150)
    if not A.skip_sensitivity:
        sensitivity(Lenticule(A.sens_sph, A.sens_cyl, A.sens_axis), A.nxy_sens, A.nz_sens, A.out, log)
    log(f'готово за {time.time() - t0:.0f} с; файлы в {A.out}/')


if __name__ == '__main__':
    main()
