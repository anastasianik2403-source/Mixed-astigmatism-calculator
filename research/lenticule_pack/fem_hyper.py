"""
fem_hyper.py — нелинейная (гиперупругая) КЭ-модель роговицы до и после удаления лентикулы, с ПРЕДВАРИТЕЛЬНЫМ НАПРЯЖЕНИЕМ.

Отличия от fem_lenticule.py (линейная упругость):
  * большие перемещения (полная лагранжева постановка, метод Ньютона с согласованной касательной матрицей);
  * гиперупругий материал:
      - 'nh'  — нео-Гук в форме Abaqus/CalculiX: W = C10 (Ī1 − 3) + (J − 1)² / D1   (C10 = μ/2, D1 = 2/K);
      - 'hgo' — нео-Гук + две семьи коллагеновых волокон в плоскости роговицы (Хольцапфель–Гассер–Огден):
                W_f = k1 / (2 k2) · (exp(k2 (I4 − 1)²) − 1), работает только при растяжении волокна (I4 > 1);
  * следящее давление (ВГД всегда перпендикулярно деформированной задней поверхности);
  * ПРЕДВАРИТЕЛЬНОЕ НАПРЯЖЕНИЕ: измеренная форма роговицы считается формой ПОД ВГД; ненапряжённая форма ищется
    обратным итерационным методом (Sellier 2011, «fixed point»): X ← X − (x(X) − x_измер), пока расхождение < 0,1 мкм;
  * операция «после» моделируется в ненапряжённой конфигурации: передняя поверхность опускается на толщину лентикулы
    (пересчитанную на ненапряжённое состояние), затем снова прикладывается ВГД.

Что НЕ моделируется (честно): эпителий и его ремоделирование, регресс, заживление, сохранённый «колпачок» SMILE
(как и в fem_lenticule.py, удаление задаётся опусканием передней поверхности), склера и податливость лимба,
вязкоупругость (важна для Corvis), неоднородность жёсткости по глубине. Параметры волокон — из литературы, иллюстративные.

Запуск:
    python3 fem_hyper.py --model nh  --E 1.0 --out out/hyper
    python3 fem_hyper.py --model hgo --mu 0.05 --k1 0.05 --k2 100 --out out/hyper_hgo
    python3 fem_hyper.py --no-prestress ...       # сравнение: геометрия «до» принята ненапряжённой (как в линейной модели)
"""
from __future__ import annotations
import argparse, os, sys, time, csv, json
from dataclasses import dataclass, field, asdict
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fem_lenticule as F
from lenticule_model import Lenticule
from skfem import MeshHex, ElementHex2, ElementVector, Basis, FacetBasis

MMHG = F.MMHG


# =============================================================================================== материалы
@dataclass
class Material:
    model: str = 'nh'           # 'nh' или 'hgo'
    C10: float = 0.172414       # МПа
    D1: float = 0.6             # 1/МПа
    k1: float = 0.0             # МПа (волокна)
    k2: float = 100.0           # безразмерный
    fib_dirs: tuple = ('x', 'y')  # две семьи волокон: проекции осей x и y на касательную плоскость (носо-височная и верх-низ)

    @staticmethod
    def from_E_nu(E, nu, **kw):
        mu = E / (2 * (1 + nu)); K = E / (3 * (1 - 2 * nu))
        return Material(C10=mu / 2, D1=2 / K, **kw)

    @property
    def mu(self): return 2 * self.C10

    @property
    def K(self): return 2 / self.D1


def stress_tangent(Fd, mat: Material, fib=None):
    """Fd: (n,3,3). Возвращает P (n,3,3) — 1-й тензор Пиолы–Кирхгофа и A = ∂P/∂F (n,3,3,3,3)."""
    n = Fd.shape[0]
    J = np.linalg.det(Fd)
    Fi = np.linalg.inv(Fd); FiT = np.swapaxes(Fi, 1, 2)            # F^{-T}
    I1 = np.einsum('nij,nij->n', Fd, Fd)
    Jm = J ** (-2.0 / 3.0)
    d = np.eye(3)
    c = 2 * mat.C10
    P = c * Jm[:, None, None] * (Fd - (I1 / 3)[:, None, None] * FiT) + (2 / mat.D1) * ((J - 1) * J)[:, None, None] * FiT
    # касательная ∂P/∂F (формулы — в README, раздел «Нелинейная модель»; проверяется конечными разностями в fem_hyper_validation.py)
    A = c * Jm[:, None, None, None, None] * (
        np.einsum('ik,JL->iJkL', d, d)[None]
        - (2 / 3) * np.einsum('nkL,niJ->niJkL', Fd, FiT)
        + (I1 / 3)[:, None, None, None, None] * np.einsum('nkJ,niL->niJkL', FiT, FiT)
        - (2 / 3) * np.einsum('nkL,niJ->niJkL', FiT, Fd - (I1 / 3)[:, None, None] * FiT))
    A += (2 / mat.D1) * (((2 * J - 1) * J)[:, None, None, None, None] * np.einsum('niJ,nkL->niJkL', FiT, FiT)
                         - ((J - 1) * J)[:, None, None, None, None] * np.einsum('nkJ,niL->niJkL', FiT, FiT))
    if mat.model == 'hgo' and fib is not None and mat.k1 > 0:
        for a in fib:                                                  # a: (n,3) единичные направления в отсчётной конфигурации
            Fa = np.einsum('niJ,nJ->ni', Fd, a)
            I4 = np.einsum('ni,ni->n', Fa, Fa)
            e = np.clip(I4 - 1, 0, None)                               # только растяжение волокна
            ex = np.exp(mat.k2 * e ** 2)
            d1 = mat.k1 * e * ex                                       # dW/dI4
            d2 = np.where(I4 > 1, mat.k1 * ex * (1 + 2 * mat.k2 * e ** 2), 0.0)   # d²W/dI4²
            P += 2 * d1[:, None, None] * np.einsum('ni,nJ->niJ', Fa, a)
            A += 2 * d1[:, None, None, None, None] * np.einsum('ik,nJ,nL->niJkL', d, a, a) \
                 + 4 * d2[:, None, None, None, None] * np.einsum('ni,nJ,nk,nL->niJkL', Fa, a, Fa, a)
    return P, A


def energy(Fd, mat: Material, fib=None):
    """Плотность энергии (для проверок)."""
    J = np.linalg.det(Fd); I1 = np.einsum('nij,nij->n', Fd, Fd)
    W = mat.C10 * (J ** (-2 / 3) * I1 - 3) + (J - 1) ** 2 / mat.D1
    if mat.model == 'hgo' and fib is not None and mat.k1 > 0:
        for a in fib:
            Fa = np.einsum('niJ,nJ->ni', Fd, a); e = np.clip(np.einsum('ni,ni->n', Fa, Fa) - 1, 0, None)
            W += mat.k1 / (2 * mat.k2) * (np.exp(mat.k2 * e ** 2) - 1)
    return W


# =============================================================================================== сетка
@dataclass
class Geo:
    mesh: MeshHex
    W: np.ndarray            # (nv,) доля толщины 0 (задняя) … 1 (передняя)
    col: np.ndarray          # (nv,) номер столбца (одинаковые U,V)
    post_facets: np.ndarray  # грани задней поверхности
    ant_facets: np.ndarray   # грани передней поверхности
    rim_facets: np.ndarray   # боковые грани (лимб)
    top: np.ndarray          # (nv,) bool — узлы передней поверхности


def build_geo(C: F.Cornea, L: Lenticule, post_op: bool, nxy: int, nz: int) -> Geo:
    u = np.linspace(-1, 1, nxy + 1); w = np.linspace(0, 1, nz + 1)
    m0 = MeshHex.init_tensor(u, u, w)
    U, V, Wt = m0.p
    xd = U * np.sqrt(1 - V ** 2 / 2) * C.r_lim; yd = V * np.sqrt(1 - U ** 2 / 2) * C.r_lim
    za = F.z_ant_pre(C, xd, yd) - (F.lent_depth(C, L, xd, yd) if post_op else 0.0)
    zp = F.z_ant_pre(C, xd, yd) - F.thickness_pre(C, xd, yd)
    z = zp + Wt * (za - zp)
    mesh = MeshHex(np.ascontiguousarray(np.vstack([xd, yd, z])), m0.t)
    key = np.round(U * 1e6).astype(np.int64) * 10 ** 8 + np.round(V * 1e6).astype(np.int64)
    _, col = np.unique(key, return_inverse=True)
    bot = Wt < 1e-12; top = Wt > 1 - 1e-12
    rim = np.hypot(xd, yd) > C.r_lim * (1 - 1e-9)
    fac = mesh.facets
    return Geo(mesh, Wt, col, np.nonzero(bot[fac].all(axis=0))[0], np.nonzero(top[fac].all(axis=0))[0],
               np.nonzero(rim[fac].all(axis=0))[0], top)


def with_points(geo: Geo, p) -> Geo:
    g = Geo(**{k: getattr(geo, k) for k in geo.__dataclass_fields__})
    g.mesh = MeshHex(np.ascontiguousarray(p), geo.mesh.t)
    return g


# =============================================================================================== сборка
class Problem:
    """Одна отсчётная (ненапряжённая) конфигурация + материал + нагрузки."""

    def __init__(self, geo: Geo, mat: Material, intorder=5):
        self.geo, self.mat = geo, mat
        self.basis = Basis(geo.mesh, ElementVector(ElementHex2()), intorder=intorder)
        b = self.basis; nloc = b.Nbfun
        G = np.stack([b.basis[i][0].grad for i in range(nloc)])             # (nloc,3,3,nel,nqp)
        self.B = np.ascontiguousarray(G.transpose(3, 4, 1, 2, 0).reshape(b.nelems, -1, 9, nloc))  # (nel,nqp,9,nloc)
        self.w = b.dx                                                        # (nel,nqp)
        self.edofs = b.element_dofs.T                                        # (nel,nloc)
        self.fib = self._fibres() if mat.model == 'hgo' else None
        self.fixed = b.get_dofs(facets=geo.rim_facets).all()
        self._fb = {}

    # --- направления волокон: проекции осей на касательную к передней поверхности купола (по координатам точки) ---
    def _fibres(self):
        X = self.basis.global_coordinates().value                           # (3,nel,nqp)
        x, y, z = [X[i].ravel() for i in range(3)]
        # нормаль сферы радиуса r_ant с центром (0,0,-r_ant)
        n = np.stack([x, y, z + 7.8]); n /= np.linalg.norm(n, axis=0)
        out = []
        for e in self.mat.fib_dirs:
            v = np.array([1.0, 0, 0] if e == 'x' else [0, 1.0, 0])[:, None]
            a = v - n * (n * v).sum(0); a /= np.linalg.norm(a, axis=0); out.append(a.T)
        return out

    def facet_basis(self, which):
        if which not in self._fb:
            fac = self.geo.post_facets if which == 'post' else self.geo.ant_facets
            fb = FacetBasis(self.geo.mesh, self.basis.elem, facets=fac, intorder=5)
            nloc = fb.Nbfun
            phi = np.stack([fb.basis[i][0].value for i in range(nloc)])     # (nloc,3,nf,nq)
            G = np.stack([fb.basis[i][0].grad for i in range(nloc)])        # (nloc,3,3,nf,nq)
            self._fb[which] = dict(fb=fb, phi=phi, G=G, edofs=fb.element_dofs.T, X=fb.global_coordinates().value)
        return self._fb[which]

    def grads(self, u):
        g = self.basis.interpolate(u).grad                                  # (3,3,nel,nqp)
        return g.transpose(2, 3, 0, 1)                                       # (nel,nqp,3,3)

    def internal(self, u, need_K=True):
        nel, nq = self.w.shape
        Fd = (np.eye(3) + self.grads(u)).reshape(-1, 3, 3)
        J = np.linalg.det(Fd)
        if J.min() <= 0:
            raise FloatingPointError('J ≤ 0: элемент вывернулся (слишком большая нагрузка/шаг)')
        fib = None if self.fib is None else [a for a in self.fib]
        P, A = stress_tangent(Fd, self.mat, fib)
        P = P.reshape(nel, nq, 9); w = self.w
        fe = np.einsum('eqk,eqkl,eq->el', P, self.B, w)                       # (nel,nloc)
        N = self.basis.N
        f = np.zeros(N); np.add.at(f, self.edofs, fe)
        if not need_K:
            return f, None
        A = A.reshape(nel, nq, 9, 9)
        AB = np.matmul(A, self.B)                                             # (nel,nq,9,nloc)
        Ke = np.einsum('eqki,eqkj,eq->eij', self.B, AB, w, optimize=True)
        I = np.broadcast_to(self.edofs[:, :, None], Ke.shape).ravel(); Jx = np.broadcast_to(self.edofs[:, None, :], Ke.shape).ravel()
        return f, sp.coo_matrix((Ke.ravel(), (I, Jx)), shape=(N, N)).tocsr()

    def pressure(self, u, which, p_fun, need_K=True):
        """Следящее давление p (МПа, может зависеть от отсчётных координат) на заднюю ('post', давит наружу-вперёд)
        или переднюю ('ant', давит внутрь) поверхность. Сила: f = −∫ p · cof(F) N · v dA (N — внешняя нормаль)."""
        d = self.facet_basis(which); fb = d['fb']
        p = p_fun(d['X'])                                                     # (nf,nq)
        g = fb.interpolate(u).grad.transpose(2, 3, 0, 1)                      # (nf,nq,3,3)
        Fd = np.eye(3) + g
        J = np.linalg.det(Fd); Fi = np.linalg.inv(Fd); FiT = np.swapaxes(Fi, -1, -2)
        Nn = fb.normals.transpose(1, 2, 0)                                    # (nf,nq,3)
        cofN = J[..., None] * np.einsum('fqiJ,fqJ->fqi', FiT, Nn)
        w = fb.dx
        fe = -np.einsum('fq,fq,fqi,lifq->fl', w, p, cofN, d['phi'])
        f = np.zeros(self.basis.N); np.add.at(f, d['edofs'], fe)
        if not need_K:
            return f, None
        # d cof(F)[H] N = J ( tr(F^-1 H) F^-T N − F^-T H^T F^-T N )
        Gj = d['G'].transpose(0, 3, 4, 1, 2)                                  # (nloc,nf,nq,3,3)
        trFH = np.einsum('fqJi,lfqiJ->lfq', Fi, Gj)
        FtN = np.einsum('fqiJ,fqJ->fqi', FiT, Nn)
        HtFtN = np.einsum('lfqmi,fqm->lfqi', Gj, FtN)                          # H^T F^-T N
        M = J[None, ..., None] * (trFH[..., None] * FtN[None] - np.einsum('fqiJ,lfqJ->lfqi', FiT, HtFtN))
        Ke = -np.einsum('fq,fq,kifq,lfqi->fkl', w, p, d['phi'], M)
        ed = d['edofs']
        I = np.broadcast_to(ed[:, :, None], Ke.shape).ravel(); Jx = np.broadcast_to(ed[:, None, :], Ke.shape).ravel()
        N = self.basis.N
        return f, sp.coo_matrix((Ke.ravel(), (I, Jx)), shape=(N, N)).tocsr()

    # --- решатель: Ньютон с пошаговым нагружением ---
    def solve(self, loads, u0=None, steps=4, tol=1e-9, maxit=25, verbose=False):
        """loads: список (which, p_fun) — давления при полной нагрузке; масштабируются линейно по шагам."""
        N = self.basis.N; u = np.zeros(N) if u0 is None else u0.copy()
        free = np.setdiff1d(np.arange(N), self.fixed)
        hist = []
        for s in range(1, steps + 1):
            lam = s / steps
            for it in range(maxit):
                f, K = self.internal(u)
                for which, pf in loads:
                    fl, Kl = self.pressure(u, which, lambda X, pf=pf: lam * pf(X))
                    f = f - fl; K = K - Kl
                r = f[free]
                nr = np.linalg.norm(r)
                if it == 0: r0 = max(nr, 1e-30)
                if verbose: print(f'  шаг {s}/{steps} ит {it}: |R| = {nr:.3e}')
                if nr < tol * max(r0, 1e-12) or nr < 1e-14:
                    break
                du = spla.spsolve(K[free][:, free].tocsc(), -r)
                u[free] += du
            else:
                raise RuntimeError(f'Ньютон не сошёлся на шаге {s}: |R| = {nr:.3e}')
            hist.append(it)
        self.newton_iters = hist
        return u

    def vertex_disp(self, u):
        return u[self.basis.nodal_dofs]                                      # (3,nv)


# =============================================================================================== обратная задача
def iop_load(C):
    p = C.iop * MMHG
    return [('post', lambda X: np.full(X.shape[1:], p))]


def stress_free(geo_meas: Geo, mat: Material, C, tol=1e-4, maxit=30, verbose=True, steps=3):
    """Ищет ненапряжённую форму X0 такую, что под ВГД она переходит в измеренную форму x_m (тол. tol мм)."""
    xm = geo_meas.mesh.p.copy(); X = xm.copy(); hist = []
    for k in range(maxit):
        pr = Problem(with_points(geo_meas, X), mat)
        u = pr.solve(iop_load(C), steps=steps)
        err = X + pr.vertex_disp(u) - xm
        e = float(np.abs(err).max()); hist.append(e)
        if verbose: print(f'  обратная задача, итерация {k + 1}: max |x(X) − x_измер| = {e * 1000:.3f} мкм')
        if e < tol:
            return X, pr, u, hist
        X = X - err
    raise RuntimeError('обратная задача не сошлась: %s' % hist)


def remove_lenticule_reference(geo_meas: Geo, X0, C, L):
    """Удаление лентикулы в НЕНАПРЯЖЁННОЙ конфигурации: глубина удаления, заданная на измеренной форме,
    пересчитывается на ненапряжённое состояние пропорционально толщине столбца (h0/hm); передняя поверхность
    опускается вдоль столбца, промежуточные слои — пропорционально доле толщины W."""
    xm = geo_meas.mesh.p; W = geo_meas.W; col = geo_meas.col
    ncol = col.max() + 1
    top = np.zeros((ncol, 3)); bot = np.zeros((ncol, 3)); topm = np.zeros((ncol, 3)); botm = np.zeros((ncol, 3))
    it = W > 1 - 1e-12; ib = W < 1e-12
    top[col[it]] = X0[:, it].T; bot[col[ib]] = X0[:, ib].T; topm[col[it]] = xm[:, it].T; botm[col[ib]] = xm[:, ib].T
    h0 = np.linalg.norm(top - bot, axis=1); hm = np.linalg.norm(topm - botm, axis=1)
    depth_m = F.lent_depth(C, L, topm[:, 0], topm[:, 1])                       # мм, на измеренной форме
    dirv = (top - bot) / h0[:, None]
    dtop = -(depth_m * h0 / hm)[:, None] * dirv
    return X0 + (W[None, :] * dtop[col].T)


# =============================================================================================== метрики
def meridian_K(geo: Geo, pts, direction, half=2.0):
    """Кератометрическая сила (дптр) передней поверхности вдоль меридиана x (0) или y (1), парабола по |s| < half."""
    x0 = geo.mesh.p                                                          # узлы выбираются по исходной (измеренной) сетке
    s0, o0 = (x0[0], x0[1]) if direction == 0 else (x0[1], x0[0])
    sel = geo.top & (np.abs(o0) < 1e-9) & (np.abs(s0) <= half + 1e-9)
    s = pts[direction][sel]; z = pts[2][sel]
    a = np.polyfit(s, z, 2)[0]
    return (F.N_KERATOMETRIC - 1) * 1000.0 / (-1.0 / (2 * a))


def delta_K(gm: Geo, pr_pre, u_pre, pr_post, u_post, X0, C, L, r_fit=2.5, removal_only=False):
    """ΔK (дптр) по плоскому (вдоль оси) и крутому меридиану из ПОЛНОГО КЭ-поля (все узлы Hex27 передней поверхности,
    не только вершины): Δz = (опускание поверхности при удалении лентикулы, по формуле толщины) + u_z(после) − u_z(до);
    по точкам r < r_fit приближается квадратичной поверхностью c0 + c1x + c2y + a x² + b y² + d xy;
    ΔK вдоль направления e = −2·(вторая производная/2 вдоль e)·(n_k − 1)·1000.
    removal_only=True — только геометрия (проверка метрики: должно быть ≈ 0,8975 × сила меридиана)."""
    from skfem import Basis as _B
    bm = _B(gm.mesh, pr_pre.basis.elem, intorder=2)                          # та же нумерация, координаты измеренной формы
    iz = bm.get_dofs(facets=gm.ant_facets).all('u^3')
    xy = bm.doflocs[:, iz]
    sel = np.hypot(xy[0], xy[1]) < r_fit; iz = iz[sel]; x, y = xy[0][sel], xy[1][sel]
    # отношение толщин столбца «ненапряжённая / измеренная» (≈1 − деформация по толщине), сглаженно по вершинам верхнего слоя
    top = gm.W > 1 - 1e-12; bot = gm.W < 1e-12
    h0 = np.zeros(gm.col.max() + 1); hm = np.zeros_like(h0); t0 = np.zeros((len(h0), 3)); b0 = np.zeros_like(t0); tm = np.zeros_like(t0); bm_ = np.zeros_like(t0)
    t0[gm.col[top]] = X0[:, top].T; b0[gm.col[bot]] = X0[:, bot].T; tm[gm.col[top]] = gm.mesh.p[:, top].T; bm_[gm.col[bot]] = gm.mesh.p[:, bot].T
    ratio = np.linalg.norm(t0 - b0, axis=1) / np.linalg.norm(tm - bm_, axis=1)
    from scipy.interpolate import griddata
    rat = griddata(tm[:, :2], ratio, np.c_[x, y], method='linear')
    dz = -F.lent_depth(C, L, x, y) * (1.0 if removal_only else rat)
    if not removal_only:
        dz = dz + u_post[iz] - u_pre[iz]
    Aq = np.c_[np.ones_like(x), x, y, x * x, y * y, x * y]
    c = np.linalg.lstsq(Aq, dz, rcond=None)[0]
    al = np.radians(L.axis)
    def k_along(t):
        e = np.array([np.cos(t), np.sin(t)])
        return -2 * (c[3] * e[0] ** 2 + c[4] * e[1] ** 2 + c[5] * e[0] * e[1]) * (F.N_KERATOMETRIC - 1) * 1000
    return k_along(al), k_along(al + np.pi / 2)


def apex_index(geo: Geo):
    p = geo.mesh.p
    return int(np.argmin(np.hypot(p[0], p[1]) + 1e3 * (~geo.top)))


def von_mises_cauchy(pr: Problem, u, r_zone):
    nel, nq = pr.w.shape
    Fd = (np.eye(3) + pr.grads(u)).reshape(-1, 3, 3)
    P, _ = stress_tangent(Fd, pr.mat, pr.fib)
    J = np.linalg.det(Fd); s = np.einsum('nij,nkj->nik', P, Fd) / J[:, None, None]
    vm = np.sqrt(0.5 * ((s[:, 0, 0] - s[:, 1, 1]) ** 2 + (s[:, 1, 1] - s[:, 2, 2]) ** 2 + (s[:, 2, 2] - s[:, 0, 0]) ** 2)
                 + 3 * (s[:, 0, 1] ** 2 + s[:, 1, 2] ** 2 + s[:, 0, 2] ** 2)).reshape(nel, nq)
    cen = pr.geo.mesh.p[:, pr.geo.mesh.t].mean(axis=1)
    return float(vm[np.hypot(cen[0], cen[1]) < r_zone].max())


# =============================================================================================== полный сценарий
def run_case(C, L, mat, nxy=12, nz=3, prestress=True, verbose=False, puff=None):
    """Возвращает словарь метрик «до/после». puff = dict(peak_mmHg, sigma_mm) — квазистатическая «струя» (для Task 2)."""
    t0 = time.time()
    gm = build_geo(C, L, False, nxy, nz)
    if prestress:
        X0, pr_pre, u_pre, hist = stress_free(gm, mat, C, verbose=verbose)
    else:
        X0 = gm.mesh.p.copy(); pr_pre = Problem(gm, mat); u_pre = pr_pre.solve(iop_load(C)); hist = []
    x_pre = X0 + pr_pre.vertex_disp(u_pre)
    X0post = remove_lenticule_reference(gm, X0, C, L) if prestress else build_geo(C, L, True, nxy, nz).mesh.p
    pr_post = Problem(with_points(gm, X0post), mat)
    u_post = pr_post.solve(iop_load(C))
    x_post = X0post + pr_post.vertex_disp(u_post)
    ia = apex_index(gm)
    ax = np.radians(L.axis); dflat = 0 if abs(np.cos(ax)) > 0.7 else 1; dsteep = 1 - dflat
    res = dict(prestress=prestress, nxy=nxy, nz=nz, dofs=pr_pre.basis.N, inverse_iters=len(hist),
               apex_shift_um=float((x_post[2, ia] - x_pre[2, ia]) * 1000),
               apex_iop_disp_pre_um=float(pr_pre.vertex_disp(u_pre)[2, ia] * 1000),
               apex_iop_disp_post_um=float(pr_post.vertex_disp(u_post)[2, ia] * 1000),
               K_flat_pre=meridian_K(gm, x_pre, dflat), K_flat_post=meridian_K(gm, x_post, dflat),
               K_steep_pre=meridian_K(gm, x_pre, dsteep), K_steep_post=meridian_K(gm, x_post, dsteep),
               Kgeo_flat=None, Kgeo_steep=None,
               vm_pre_kPa=von_mises_cauchy(pr_pre, u_pre, L.R) * 1000, vm_post_kPa=von_mises_cauchy(pr_post, u_post, L.R) * 1000)
    # ΔK из полного поля (основная метрика) и «только геометрия» той же метрикой; построчная оценка по вершинам — справочно
    res['dK_flat_nodes'] = res['K_flat_post'] - res['K_flat_pre']; res['dK_steep_nodes'] = res['K_steep_post'] - res['K_steep_pre']
    res['dK_flat'], res['dK_steep'] = delta_K(gm, pr_pre, u_pre, pr_post, u_post, X0, C, L)
    res['Kgeo_flat'], res['Kgeo_steep'] = delta_K(gm, pr_pre, u_pre, pr_post, u_post, X0 if prestress else gm.mesh.p, C, L, removal_only=True)
    if puff:
        res['S_pre'] = puff_stiffness(pr_pre, u_pre, C, **puff)
        res['S_post'] = puff_stiffness(pr_post, u_post, C, **puff)
    res['time_s'] = time.time() - t0
    res['_fields'] = dict(gm=gm, X0=X0, x_pre=x_pre, x_post=x_post, X0post=X0post)
    return res


def puff_stiffness(pr: Problem, u_iop, C, peak_mmHg=10.0, sigma_mm=1.5):
    """Квазистатический аналог SP-A1: к нагруженной ВГД роговице добавляется давление «струи» на переднюю поверхность
    p(r) = peak·exp(−r²/2σ²); жёсткость S = peak / (смещение вершины назад), мм рт. ст./мм.
    ЭТО НЕ динамика Corvis (нет инерции, вязкости, аппланации) — только монотонный суррогат жёсткости."""
    pk = peak_mmHg * MMHG
    loads = iop_load(C) + [('ant', lambda X: pk * np.exp(-(X[0] ** 2 + X[1] ** 2) / (2 * sigma_mm ** 2)))]
    u = pr.solve(loads, u0=u_iop, steps=2)
    ia = apex_index(pr.geo)
    d = (pr.vertex_disp(u_iop)[2, ia] - pr.vertex_disp(u)[2, ia])
    return float(peak_mmHg / d)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sph', type=float, default=1.0); ap.add_argument('--cyl', type=float, default=-4.0)
    ap.add_argument('--axis', type=float, default=0.0); ap.add_argument('--oz', type=float, default=6.7); ap.add_argument('--tmin', type=float, default=20.0)
    ap.add_argument('--iop', type=float, default=15.0); ap.add_argument('--cct', type=float, default=0.54); ap.add_argument('--r-ant', type=float, default=7.8)
    ap.add_argument('--model', choices=['nh', 'hgo'], default='nh')
    ap.add_argument('--E', type=float, default=1.0); ap.add_argument('--nu', type=float, default=0.45)
    ap.add_argument('--mu', type=float, default=None, help='модуль сдвига матрицы (для hgo), МПа')
    ap.add_argument('--k1', type=float, default=0.05); ap.add_argument('--k2', type=float, default=100.0)
    ap.add_argument('--nxy', type=int, default=12); ap.add_argument('--nz', type=int, default=3)
    ap.add_argument('--no-prestress', action='store_true'); ap.add_argument('--out', default='out/hyper')
    A = ap.parse_args()
    C = F.Cornea(r_ant=A.r_ant, cct=A.cct, E=A.E, nu=A.nu, iop=A.iop); L = Lenticule(A.sph, A.cyl, A.axis, A.oz, A.tmin)
    if A.model == 'nh':
        mat = Material.from_E_nu(A.E, A.nu)
    else:
        mu = A.mu if A.mu is not None else A.E / (2 * (1 + A.nu))
        K = 2 * mu * (1 + A.nu) / (3 * (1 - 2 * A.nu))
        mat = Material(model='hgo', C10=mu / 2, D1=2 / K, k1=A.k1, k2=A.k2)
    os.makedirs(A.out, exist_ok=True)
    print(L.summary()); print('материал:', asdict(mat))
    r = run_case(C, L, mat, A.nxy, A.nz, prestress=not A.no_prestress, verbose=True)
    r.pop('_fields')
    for k, v in r.items(): print(f'  {k}: {v:.4f}' if isinstance(v, float) else f'  {k}: {v}')
    with open(f'{A.out}/results_hyper.json', 'w', encoding='utf-8') as f:
        json.dump(dict(params=vars(A), material=asdict(mat), results=r), f, ensure_ascii=False, indent=1,
                  default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print('файл:', f'{A.out}/results_hyper.json')


if __name__ == '__main__':
    main()
