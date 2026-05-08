#!/bin/bash
python -u /home/poyen/ef-md-workflow-main/3_MLP_MD_with_E/MLP_MD_E_only_MACE_new.py \
    --input "structure.xyz" \
    --MLP_model "/home/poyen/BTO_MLFF/MACE/MACE_large_100.model" \
    --ini_temperature 250 \
    --total_step 600000 \
    --device "cuda" \
    --ensemble_type "NPT" \
    --BEC_model "/home/poyen/BTO_MLFF/MACE/MACEField_from_BTO/MACE_Field.model" \
    --efield_mode "triangle" \
    --bec_update_interval 10 \
    --efield_direction "x" \
    --ref ./POSCAR_ref \
    --Emax 0.0015 \
#    --positive_first \
#    --Elist -0.15000 \
