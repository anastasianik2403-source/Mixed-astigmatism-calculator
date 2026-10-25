#!/usr/bin/env bash
# Полный прогон: проверки → геометрия → КЭ-расчёт (линейный и нелинейный) → файлы для ANSYS/CalculiX → калибровка Corvis.
# Blender — отдельной командой (см. README). Время: линейная часть ~1 мин; нелинейные проверки ~15 мин; калибровка ~30–60 мин.
set -e
cd "$(dirname "$0")"
python3 lenticule_model.py --selftest
python3 lenticule_model.py --exag 8 --out out/geometry
python3 fem_validation.py
python3 fem_lenticule.py --out out/fem
python3 fe_export.py --out out/fe_decks
if [ "${QUICK:-0}" = "1" ]; then echo "QUICK=1: нелинейная часть пропущена"; exit 0; fi
python3 fem_hyper_validation.py --out out/hyper_validation            # проверки нелинейного решателя (+ CalculiX, если установлен)
python3 fem_hyper.py --model nh  --out out/hyper_nh                    # нео-Гук + преднапряжение
python3 fem_hyper.py --model hgo --mu 0.05 --k1 0.05 --k2 100 --out out/hyper_hgo   # + коллагеновые волокна (иллюстративные параметры)
python3 calibrate_corvis.py --eyes examples/corvis_demo_eyes.csv --out out/corvis   # ДЕМО-глаза; свои данные — свой CSV
echo "Готово. Результаты в папке out/"
echo "Blender:  python3 blender_lenticule.py --labels --video --out out/blender/podpisi   (или blender -b -P blender_lenticule.py -- ...)"
