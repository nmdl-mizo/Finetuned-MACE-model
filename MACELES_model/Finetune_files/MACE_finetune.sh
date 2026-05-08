#!/bin/bash
mace_run_train \
    --name="MACE_fintune" \
    --foundation_model="large" \
    --train_file="train.xyz" \
    --valid_fraction=0.05 \
    --energy_weight=1.0 \
    --forces_weight=1.0 \
    --E0s="average" \
    --lr=0.01 \
    --scaling="rms_forces_scaling" \
    --batch_size=8 \
    --max_num_epochs=100 \
    --valid_batch_size=8\
    --ema \
    --ema_decay=0.99 \
    --amsgrad \
    --default_dtype="float64" \
    --device=cuda \
    --seed=3\
    --save_cpu\
    --patience=5\
    --swa\
    --forces_key='forces'\
    --energy_key='energy'\
    #--becs_key='becs'


    