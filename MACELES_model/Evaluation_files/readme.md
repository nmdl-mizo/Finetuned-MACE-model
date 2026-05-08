# Energy and Force Prediction

Energy and force validation can be performed using the provided Python script `validation.py`.

```bash
python validation.py \
  --xyz_file <your/test/data> \
  --MLP_model "../BTO_MACELES.model" \
  --compute_ef \
  --plot_energy \
  --plot_forces
```

# Phonon Calculation

Phonon dispersion calculations can be performed using `MACE_phonon_2.py`.

```bash
python MACE_phonon_2.py
```

# Elastic Constant Calculation

The elastic constants can be calculated using:

```bash
python calc_elastic_constant.py
```

# MD Simulation

MD simulations under an applied electric field can be executed using the bash script `run_MD.sh`.

```bash
bash run_MD.sh
```

More information about MD simulations under applied electric fields and the required environment setup can be found in the [ef-md-workflow](https://github.com/nmdl-mizo/ef-md-workflow.git) repository.
