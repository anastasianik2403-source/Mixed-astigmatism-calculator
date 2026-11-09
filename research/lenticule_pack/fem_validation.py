"""
fem_validation.py — проверка конечно-элементного решателя (fem_lenticule.py) по аналитическим решениям.
  1) Круглая пластина, жёстко защемлённая по краю, равномерное давление: прогиб в центре
     w = p·a⁴/(64·D) + p·a²/(4·κ·G·t)   (Кирхгоф + поправка на сдвиг, κ = 5/6).
  2) Пологий сферический купол постоянной толщины, защемлён по краю, давление изнутри: теория пологих оболочек
     (Рейсснер; решение через функции Кельвина ber/bei) — прогиб в вершине.
Допуск: пластина ±5 %, оболочка ±10 % (теория пологих оболочек приближённая, радиус срединной поверхности неоднозначен).
Запуск: python3 fem_validation.py
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem_lenticule as F
from lenticule_model import Lenticule
from scipy.special import ber, bei, berp, beip
from scipy.integrate import quad

L = Lenticule(0, 0, 0, 6.7, 20)


def apex_dz(C, nxy, nz):
    mesh, basis, u, _ = F.solve_case(C, L, False, nxy, nz, iterative=True)
    U = u[basis.nodal_dofs]; on = F.surface_nodes(mesh, C, L, False)
    return float(U[2][np.argmin(np.hypot(mesh.p[0], mesh.p[1]) + 1e3 * (~on))])


def plate():
    C = F.Cornea(r_ant=1e9, cct=0.54, t_per=0.54, E=1.0, nu=0.3, iop=15)
    a, t, p = C.r_lim, C.cct, C.iop * F.MMHG
    D = C.E * t ** 3 / (12 * (1 - C.nu ** 2)); G = C.E / (2 * (1 + C.nu))
    ref = p * a ** 4 / (64 * D) + p * a ** 2 / (4 * (5 / 6) * G * t)
    fe = apex_dz(C, 16, 3)
    print(f'пластина: КЭ {fe:.4f} мм, аналитика {ref:.4f} мм, отношение {fe / ref:.3f}')
    return abs(fe / ref - 1) < 0.05


def shell():
    C = F.Cornea(cct=0.54, t_per=0.54, E=1.0, nu=0.45, iop=15)
    E, nu, t, p, a = C.E, C.nu, C.cct, C.iop * F.MMHG, C.r_lim
    out = []
    for Rm in (C.r_ant, C.r_ant - t / 2):                # радиус внешней и срединной поверхности
        m = (12 * (1 - nu ** 2)) ** 0.25 / np.sqrt(t * Rm); c0 = p * Rm ** 2 / (E * t); k = E * t / (Rm * a ** 2)
        Ib = quad(lambda r: r * ber(m * r), 0, a)[0]; Ii = quad(lambda r: r * bei(m * r), 0, a)[0]
        M = np.array([[ber(m * a), bei(m * a), -Rm / (E * t)], [m * berp(m * a), m * beip(m * a), 0.0],
                      [-(1 + nu) * k * Ib, -(1 + nu) * k * Ii, 1 - (1 + nu) * (k * (-Rm / (E * t)) * a ** 2 / 2 + 0.5)]])
        b = np.array([-c0, 0.0, (1 + nu) * k * c0 * a ** 2 / 2])
        A, B, C1 = np.linalg.solve(M, b); out.append((c0 - C1 * Rm / (E * t) + A))
    fe = apex_dz(C, 16, 3)
    print(f'купол: КЭ {fe * 1000:.1f} мкм, теория пологих оболочек {out[1] * 1000:.1f}–{out[0] * 1000:.1f} мкм')
    return min(out) * 0.9 < fe < max(out) * 1.1


if __name__ == '__main__':
    ok = plate() & shell()
    print('ПРОВЕРКА ПРОЙДЕНА' if ok else 'ПРОВЕРКА НЕ ПРОЙДЕНА'); raise SystemExit(0 if ok else 1)
