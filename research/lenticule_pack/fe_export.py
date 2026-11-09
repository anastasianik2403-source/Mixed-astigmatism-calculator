"""
fe_export.py — выгрузка той же гексаэдральной сетки (роговица до/после удаления лентикулы) в форматы коммерческих и
открытых КЭ-программ, чтобы расчёт можно было повторить и УСЛОЖНИТЬ там (нелинейная гиперупругость, предварительное
напряжение, анизотропия коллагена):
    ansys_pre.inp / ansys_post.inp  — APDL-скрипт для ANSYS Mechanical APDL  (SOLID185, мм–Н–МПа)
    calculix_pre.inp / calculix_post.inp — формат Abaqus/CalculiX (C3D8)
    cornea_pre.vtu / cornea_post.vtu — для ParaView (просмотр сетки)

ВАЖНО (честно): в этой среде НЕТ ни ANSYS, ни CalculiX, поэтому сами файлы НЕ запускались в этих программах.
Что проверено автоматически: узлы и элементы записаны и читаются обратно, у всех элементов положительный якобиан
(порядок узлов правильный), грани давления лежат на задней поверхности, закреплены именно узлы лимба.
Синтаксис команд — по документации ANSYS/CalculiX; при первом запуске посмотрите сообщения о предупреждениях.

Запуск:  python3 fe_export.py --sph 1.0 --cyl -4.0 --axis 0 --E 1.0 --nu 0.45 --iop 15 --out fe_decks
В ANSYS:  /INPUT,ansys_pre,inp   затем   /INPUT,ansys_post,inp   (результат — файл *.rst и текстовые таблицы смещений)
В CalculiX:  ccx calculix_pre   и   ccx calculix_post
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem_lenticule as F
from lenticule_model import Lenticule

# skfem: вершины гексаэдра (0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,1,1)
# ANSYS/Abaqus: 1-4 — нижняя грань против часовой стрелки, 5-8 — над ними в том же порядке
SK2STD = [0, 1, 4, 2, 3, 5, 7, 6]


def std_hex(mesh):
    """Порядок узлов ANSYS/Abaqus. Нижняя грань (узлы 1-4) — задняя поверхность (слой w=0), верхняя (5-8) — передняя.
    Отображение квадрат→круг в сетке зеркалит плоскость (x, y), поэтому подбираем порядок обхода по знаку якобиана."""
    p = mesh.p.T
    for order in ([0, 1, 4, 2, 3, 5, 7, 6], [0, 2, 4, 1, 3, 6, 7, 5]):
        t = mesh.t[order].T.copy()
        if jacobian_ok(p, t).all():
            return t
    raise RuntimeError('не удалось подобрать ориентацию элементов (смешанный знак якобиана)')


def jacobian_ok(p, t):
    c = lambda k: p[t[:, k]]
    # якобиан в центре элемента: det[∂x/∂ξ, ∂x/∂η, ∂x/∂ζ] с ξ вдоль 1→2, η вдоль 1→4, ζ вдоль 1→5 (усреднённые по 4 рёбрам)
    dx = ((c(1) - c(0)) + (c(2) - c(3)) + (c(5) - c(4)) + (c(6) - c(7))) / 4
    dy = ((c(3) - c(0)) + (c(2) - c(1)) + (c(7) - c(4)) + (c(6) - c(5))) / 4
    dz = ((c(4) - c(0)) + (c(5) - c(1)) + (c(6) - c(2)) + (c(7) - c(3))) / 4
    return np.einsum('ij,ij->i', np.cross(dx, dy), dz) > 0


def write_decks(C, L, post, nxy, nz, out):
    mesh, _ = F.build_mesh(C, L, post, nxy, nz)
    p = mesh.p.T; t = std_hex(mesh)
    assert jacobian_ok(p, t).all(), 'отрицательный якобиан'
    tag = 'post' if post else 'pre'
    zp = F.z_ant_pre(C, p[:, 0], p[:, 1]) - F.thickness_pre(C, p[:, 0], p[:, 1])
    post_node = np.abs(p[:, 2] - zp) < 1e-9
    rim = np.hypot(p[:, 0], p[:, 1]) > C.r_lim * (1 - 1e-9)
    # элементы нижнего слоя: у них нижняя грань (узлы 1-4) лежит на задней поверхности → грань 1 (ANSYS: SFE,...,1 ; Abaqus: P1)
    bottom_el = np.nonzero(post_node[t[:, :4]].all(axis=1))[0]
    assert len(bottom_el) == (nxy * nxy), (len(bottom_el), nxy * nxy)
    mu = C.E / (2 * (1 + C.nu)); K = C.E / (3 * (1 - 2 * C.nu)); P = C.iop * F.MMHG
    title = f'Роговица {"после" if post else "до"} удаления лентикулы: Sph {L.sph:+.2f} Cyl {L.cyl:+.2f} ось {L.axis:.0f}'
    # ---------------- ANSYS APDL ----------------
    with open(f'{out}/ansys_{tag}.inp', 'w', encoding='utf-8') as f:
        f.write(f'! {title}\n! Единицы: мм, Н, МПа. Сгенерировано fe_export.py. НЕ запускалось в ANSYS (нет лицензии) — проверьте при первом запуске.\n')
        f.write('/CLEAR,NOSTART\n/FILNAME,cornea_%s,1\n/PREP7\nET,1,SOLID185\nKEYOPT,1,6,1      ! смешанная u-P формулировка (нужна для почти несжимаемого материала)\n' % tag)
        f.write(f'MP,EX,1,{C.E}\nMP,PRXY,1,{C.nu}\n')
        f.write('! Для гиперупругого материала вместо двух строк выше (нео-Гук, начальный модуль сдвига mu и параметр сжимаемости d=2/K):\n')
        f.write(f'! TB,HYPER,1,1,1,NEO\n! TBDATA,1,{mu:.6f},{2 / K:.6f}\n')
        f.write('TYPE,1\nMAT,1\n')
        for i, (x, y, z) in enumerate(p, 1): f.write(f'N,{i},{x:.6f},{y:.6f},{z:.6f}\n')
        for r in t + 1: f.write('E,' + ','.join(str(k) for k in r) + '\n')
        f.write('! --- закрепление лимба (все степени свободы) ---\n')
        for i in np.nonzero(rim)[0] + 1: f.write(f'D,{i},ALL,0\n')
        f.write(f'! --- давление ВГД {C.iop:.0f} мм рт. ст. = {P:.6f} МПа на заднюю поверхность (грань 1 элементов нижнего слоя) ---\n')
        for e in bottom_el + 1: f.write(f'SFE,{e},1,PRES,,{P:.8f}\n')
        f.write('FINISH\n/SOLU\nANTYPE,STATIC\nNLGEOM,ON        ! большие перемещения; для чисто линейного сравнения поставьте OFF\nNSUBST,10,50,5\nAUTOTS,ON\nOUTRES,ALL,ALL\nSOLVE\nFINISH\n')
        f.write('/POST1\nSET,LAST\n*CFOPEN,disp_%s,txt\n*VWRITE,\'node\',\'x\',\'y\',\'z\',\'UZ\'\n(A6,4A14)\n' % tag)
        f.write('*GET,nmax,NODE,0,NUM,MAX\n*DO,i,1,nmax\n*GET,xx,NODE,i,LOC,X\n*GET,yy,NODE,i,LOC,Y\n*GET,zz,NODE,i,LOC,Z\n*GET,uz,NODE,i,U,Z\n*VWRITE,i,xx,yy,zz,uz\n(F8.0,4E14.6)\n*ENDDO\n*CFCLOS\n')
    # ---------------- CalculiX / Abaqus ----------------
    with open(f'{out}/calculix_{tag}.inp', 'w', encoding='utf-8') as f:
        f.write(f'** {title}\n** Единицы: мм, Н, МПа. Сгенерировано fe_export.py. НЕ запускалось в CalculiX (нет программы в среде).\n*NODE\n')
        for i, (x, y, z) in enumerate(p, 1): f.write(f'{i},{x:.6f},{y:.6f},{z:.6f}\n')
        f.write('*ELEMENT,TYPE=C3D8,ELSET=CORNEA\n')
        for i, r in enumerate(t + 1, 1): f.write(f'{i},' + ','.join(str(k) for k in r) + '\n')
        f.write('*NSET,NSET=LIMBUS\n'); ids = list(np.nonzero(rim)[0] + 1)
        for k in range(0, len(ids), 12): f.write(','.join(map(str, ids[k:k + 12])) + '\n')
        za_nodes = np.abs(p[:, 2] - (F.z_ant_pre(C, p[:, 0], p[:, 1]) - (F.lent_depth(C, L, p[:, 0], p[:, 1]) if post else 0.0))) < 1e-9
        apex_id = int(np.nonzero(za_nodes & (np.hypot(p[:, 0], p[:, 1]) < 1e-9))[0][0] + 1)
        f.write(f'*NSET,NSET=APEX\n{apex_id}\n')
        f.write('*ELSET,ELSET=POSTERIOR\n'); ids = list(bottom_el + 1)
        for k in range(0, len(ids), 12): f.write(','.join(map(str, ids[k:k + 12])) + '\n')
        f.write(f'*MATERIAL,NAME=STROMA\n*ELASTIC\n{C.E},{C.nu}\n*SOLID SECTION,ELSET=CORNEA,MATERIAL=STROMA\n')
        f.write('** Для гиперупругости вместо *ELASTIC: *HYPERELASTIC,NEO HOOKE  /  C10, D1  (C10 = mu/2, D1 = 2/K)\n')
        f.write(f'** C10 = {mu / 2:.6f}, D1 = {2 / K:.6f}\n*BOUNDARY\nLIMBUS,1,3,0\n*STEP,NLGEOM,INC=100\n*STATIC\n0.1,1.0\n')
        f.write(f'*DLOAD\nPOSTERIOR,P1,{P:.8f}\n*NODE FILE\nU\n*NODE PRINT,NSET=APEX\nU\n*END STEP\n')
    # ---------------- VTK ----------------
    try:
        import meshio
        meshio.write(f'{out}/cornea_{tag}.vtu', meshio.Mesh(p, [('hexahedron', t[:, [0, 1, 2, 3, 4, 5, 6, 7]])]))
    except Exception as e:
        print('VTK пропущен:', e)
    # ---------------- обратная проверка записанного ----------------
    n_nodes = sum(1 for l in open(f'{out}/ansys_{tag}.inp', encoding='utf-8') if l.startswith('N,'))
    n_el = sum(1 for l in open(f'{out}/ansys_{tag}.inp', encoding='utf-8') if l.startswith('E,'))
    n_fix = sum(1 for l in open(f'{out}/ansys_{tag}.inp', encoding='utf-8') if l.startswith('D,'))
    n_prs = sum(1 for l in open(f'{out}/ansys_{tag}.inp', encoding='utf-8') if l.startswith('SFE,'))
    assert n_nodes == len(p) and n_el == len(t) and n_fix == rim.sum() and n_prs == len(bottom_el)
    print(f'{tag}: узлов {n_nodes}, элементов {n_el}, закреплено узлов {n_fix}, граней под давлением {n_prs}; якобиан > 0 у всех элементов')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0); ap.add_argument('--axis', type=float, default=0.0)
    ap.add_argument('--oz', type=float, default=6.7); ap.add_argument('--tmin', type=float, default=20.0)
    ap.add_argument('--E', type=float, default=1.0); ap.add_argument('--nu', type=float, default=0.45); ap.add_argument('--iop', type=float, default=15.0)
    ap.add_argument('--nxy', type=int, default=16); ap.add_argument('--nz', type=int, default=3); ap.add_argument('--out', default='fe_decks')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    C = F.Cornea(E=A.E, nu=A.nu, iop=A.iop); L = Lenticule(A.sph, A.cyl, A.axis, A.oz, A.tmin)
    for post in (False, True): write_decks(C, L, post, A.nxy, A.nz, A.out)
    print('файлы в', A.out)
