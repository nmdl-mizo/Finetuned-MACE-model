import numpy as np
import glob, os
import argparse
from ase.io import read
from mace.calculators import mace_mp
import matplotlib.pyplot as plt
import torch
#from equivar_eval.scripts.calculate import Calculate, MACECalculator

# ----------------------
# Utils
# ----------------------
def flatten(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, (list, np.ndarray)):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list

# ----------------------
# Main
# ----------------------
def main(args):
    structure_list = []
    energy_list = []
    forces_list = []
    ML_energy_list = []
    ML_forces_list = []

    becs_list = []
    ML_becs_list = []
    for file in args.xyz_file:
        structures = read(file, index = ":")
        structure_list.extend(structures)
        
    # MACE calculator
    if args.compute_ef:
        #calc = mace_mp(model=args.MLP_model,device=args.device)
        calc = MACECalculator(model=args.MLP_model,device=args.device, enable_cueq=True)
        energy_list = []
        forces_list = []
        ML_energy_list = []
        ML_forces_list = []
        for structure in structure_list:
            structure.calc = calc
            force = structure.get_forces()
            energy = structure.get_potential_energy()
            energy_list.append(float(structure.info["energy"])/len(structure))
            forces_list.append(structure.arrays["forces"])
            ML_energy_list.append((energy) / len(structure))
            ML_forces_list.append(force)

        # MAE
        E_MAE = [
            abs(energy_list[i] - ML_energy_list[i])
            for i in range(len(energy_list))
        ]

        F_MAE = [
            np.mean(np.abs(np.array(forces_list[i]) - np.array(ML_forces_list[i])))
            for i in range(len(forces_list))
        ]
        print(f"Energy MAE = {np.mean(E_MAE):.6f} eV/atom")
        print(f"Force MAE  = {np.mean(F_MAE):.6f} eV/Å")

    if args.compute_becs:
        model=torch.jit.load(args.BEC_model ,map_location=torch.device(args.device))
        model.eval()
        becs_list = []
        ML_becs_list = []
        for structure in structure_list:
            becs_list.append(structure.arrays["becs"])
            ML_becs = Calculate(structure, model)
            ML_becs_list.append(ML_becs.cpu().numpy())
        BEC_MAE = [
            np.mean(np.abs(np.array(becs_list[i]) - np.array(ML_becs_list[i])))
            for i in range(len(becs_list))
        ]
        print(f"BECs MAE = {np.mean(BEC_MAE):.6f} e")
            
    if args.plot_energy:
        plt.figure(dpi=300, figsize=(5.5, 5.5))
        plt.scatter(energy_list,ML_energy_list)
        min_value = min(min(energy_list), min(ML_energy_list))
        max_value = max(max(energy_list), max(ML_energy_list))
        plt.plot([min_value-1, max_value+1], [min_value-1, max_value+1], "k--")
        plt.xlabel("Energy by DFT (eV/atom)")
        plt.ylabel("Energy by MLP (eV/atom)")
        plt.xlim(min_value-0.1, max_value+0.1)
        plt.ylim(min_value-0.1, max_value+0.1)
        plt.savefig("energy_comparison.png", bbox_inches="tight")

    if args.plot_forces:
        plt.figure(dpi=300, figsize=(5.5, 5.5))
        flatten_forces_list = flatten(forces_list)
        flatten_ML_forces_list = flatten(ML_forces_list)
        plt.scatter(flatten_forces_list,flatten_ML_forces_list)
        min_value = min(min(flatten_forces_list), min(flatten_ML_forces_list))
        max_value = max(max(flatten_forces_list), max(flatten_ML_forces_list))
        plt.plot([min_value-1, max_value+1], [min_value-1, max_value+1], "k--")
        plt.xlabel("Force by DFT (eV/Å)")
        plt.ylabel("Force by MLP (eV/Å)")
        plt.xlim(min_value-1, max_value+1)
        plt.ylim(min_value-1, max_value+1)
        plt.savefig("forces_comparison.png", bbox_inches="tight")

    if args.plot_becs:
        plt.figure(dpi=300, figsize=(5.5, 5.5))
        flatten_becs_list = flatten(becs_list)
        flatten_ML_becs_list = flatten(ML_becs_list)
        plt.scatter(flatten_becs_list,flatten_ML_becs_list)
        min_value = min(min(flatten_becs_list), min(flatten_ML_becs_list))
        max_value = max(max(flatten_becs_list), max(flatten_ML_becs_list))
        plt.plot([min_value-0.5, max_value+0.5], [min_value-0.5, max_value+0.5], "k--")
        plt.xlabel("BECs by DFPT (e)")
        plt.ylabel("BECs by ML (e)")
        plt.xlim(min_value-0.5, max_value+0.5)
        plt.ylim(min_value-0.5, max_value+0.5)
        plt.savefig("becs_comparison.png", bbox_inches="tight")

# ----------------------
# argparse
# ----------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Benchmark MLP (MACE) vs DFT for energy / forces / BECs"
    )

    # ---------- input ----------
    parser.add_argument(
        "--xyz_file",
        nargs="+",
        required=True,
        help="Extended XYZ file(s) containing DFT energy / forces / becs"
    )
    parser.add_argument(
        "--compute_ef",
        action="store_true",
        help="Compute energy and force using MLP model"
    )
    parser.add_argument(
        "--MLP_model",
        type=str,
        default=None,
        help="Path to trained MACE model"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cpu", "cuda"],
        help="Device for inference"
    )

    # ---------- BEC ----------
    parser.add_argument(
        "--compute_becs",
        action="store_true",
        help="Compute BECs using ML model"
    )

    parser.add_argument(
        "--BEC_model",
        type=str,
        default=None,
        help="Path to trained BEC ML model (required if --compute_becs)"
    )

    # ---------- plotting ----------
    parser.add_argument(
        "--plot_energy",
        action="store_true",
        help="Plot DFT vs MLP energy parity"
    )

    parser.add_argument(
        "--plot_forces",
        action="store_true",
        help="Plot DFT vs MLP force parity"
    )

    parser.add_argument(
        "--plot_becs",
        action="store_true",
        help="Plot DFPT vs ML BEC parity"
    )

    args = parser.parse_args()

    # ---------- sanity checks ----------
    if args.compute_becs and args.BEC_model is None:
        parser.error("--compute_becs requires --BEC_model")
    
    if args.compute_ef and args.MLP_model is None:
        parser.error("--compute_ef requires --MLP_model")

    if args.plot_becs and not args.compute_becs:
        parser.error("--plot_becs requires --compute_becs")
    
    if args.plot_energy and not args.compute_ef:
        parser.error("--plot_energy requires --compute_ef")
    if args.plot_forces and not args.compute_ef:
        parser.error("--plot_forces requires --compute_ef")
    if not args.compute_becs and not args.compute_ef:
        parser.error("Please input --compute_ef or --compute_becs to start validation.")

    main(args)