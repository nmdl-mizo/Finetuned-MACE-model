#!/bin/bash
python -u ./MLP_MD_E.py \
    --input "POSCAR" \
    --MLP_model "../BTO_MACELES.model" \
    --ini_temperature 250 \
    --total_step 400000 \
    --device "cuda" \
    --ensemble_type "NPT" \
    --BEC_model "../BTO_Equivar_model.model" \
    --efield_mode "triangle" \
    --bec_update_interval 10 \
    --efield_direction "x" \
    --Emax 0.00100 \
    --use_Equivar
