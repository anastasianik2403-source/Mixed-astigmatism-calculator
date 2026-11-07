"""Единый спокойный стиль рисунков лентикулы: мягкая сине-серая шкала толщины, меридианы — бирюзовый (плоский) и
терракотовый (крутой): различимы и при нарушениях цветового зрения; линии с белым ореолом, чтобы читались на любом фоне."""
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe

LENT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    'lenticule_calm', ['#f4f8fb', '#d6e6f2', '#a9c9e3', '#7aa8cf', '#4f84b3', '#2f5f8c', '#1e3f5f'])
CORNEA_CMAP = mcolors.LinearSegmentedColormap.from_list('cornea_calm', ['#eef3ef', '#c9ddd0', '#93bba5', '#5e9479', '#356b54'])
FLAT_COL = '#178a73'      # плоский меридиан (наибольшая толщина)
STEEP_COL = '#d0613f'     # крутой меридиан (наименьшая толщина)
PLAN_COL = '#8a94a3'      # план VisuMax
MODEL_B_COL = '#6b5ca5'   # модель «план → реальность»
HALO = [pe.Stroke(linewidth=4.6, foreground='white'), pe.Normal()]
