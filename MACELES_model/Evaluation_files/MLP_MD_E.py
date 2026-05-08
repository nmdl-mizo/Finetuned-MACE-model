import argparse
import time, datetime
import ast
import numpy as np
import torch
import ase
import ase.io
from ase import units
from ase.md.npt_addF import NPT
from ase.md.langevin_addF import Langevin
from ase.md.nvtberendsen_addF import NVTBerendsen
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.constraints import FixCom
from ase.md import MDLogger
from ase.io.trajectory import Trajectory
from mace.calculators import mace_mp, MACECalculator
#

# =====================
# argparse
# =====================
def parse_args():
    parser = argparse.ArgumentParser(description="ASE + MACE MD with optional electric field")

    # ---- MD basics ----
    parser.add_argument("--input", type = str, required=True)
    parser.add_argument("--MLP_model", type = str, required = True)
    parser.add_argument("--BEC_model", type = str, default = None)
    parser.add_argument("--use_Equivar", action="store_true")
    parser.add_argument("--ini_temperature", type=float, required=True)
    parser.add_argument("--total_step", type=int, required=True)
    parser.add_argument("--ref", type = str, default=None)
    parser.add_argument("--device", type = str, default="cuda")
    parser.add_argument("--timestep", type=float, default=1.0)
    parser.add_argument("--fin_temperature", type=float, default = None)
    parser.add_argument("--traj_interval", type=int, default = 1000)

    # ---- ensemble type ----
    parser.add_argument(
        "--ensemble_type",
        choices=["NPT", "Langevin", "NVTBerendsen"],
        default="NPT",
        help="Ensemble type (default: NPT)"
    )

    # ---- NPT setting ----
    parser.add_argument("--ttime", type=float, default = 25)
    parser.add_argument("--ptime", type=float, default = 75)
    parser.add_argument("--N", type=int, default = 10000)
    parser.add_argument(
        "--externalstress",
        type=str,
        default="0.0",
        help=(
            "External stress. "
            "Examples:\n"
            "  0.0\n"
            "  'sx sy sz'\n"
            "  'sxx syy szz syz sxz sxy'\n"
            "  '[[sxx,sxy,sxz],[syx,syy,syz],[szx,szy,szz]]'"
        )
    )
    parser.add_argument(
        "--mask",
        type=str,
        default=None,
        help="Mask: None, 'x y z', or '[[a,b,c],[d,e,f],[g,h,i]]'"
    )   

    # ---- Langevin setting ----
    parser.add_argument("--friction", type=float, default= 0.01)

    # ---- NVTBerendsen setting ----
    parser.add_argument("--taut", type=float, default = 500)

    # ---- electric field mode ----
    parser.add_argument(
        "--efield_mode",
        choices=["none", "triangle", "step"],
        default="none",
        help="Electric field mode (default: none)"
    )
    
    # ---- BEC update interval ----
    parser.add_argument("--bec_update_interval", type=int, default = 10) 

    # ---- electric field direction ----
    parser.add_argument(
        "--efield_direction",
        choices=["x", "y", "z", "xy", "xz", "yz", "xyz"],
        default="z",
        help="Electric field direction (default: z)"
    )
    
    # ---- triangle field ----
    parser.add_argument("--Emax", type=float, default=0.0)
    parser.add_argument("--positive_first", action="store_true")

    # ---- step field ----
    parser.add_argument("--Elist", type=float, nargs="+", default=[0])

    return parser.parse_args()


def parse_mask(mask_str):
    if mask_str is None:
        return None

    # case 1: "1 0 1"
    if " " in mask_str and "[" not in mask_str:
        values = tuple(float(x) for x in mask_str.split())
        if len(values) != 3:
            raise ValueError("Mask tuple must have exactly 3 values")
        return values

    # case 2: "[[...],[...],[...]]"
    try:
        mat = np.array(ast.literal_eval(mask_str))
        if mat.shape != (3, 3):
            raise ValueError("Mask matrix must be 3x3")
        return mat
    except Exception:
        raise ValueError(f"Cannot parse mask: {mask_str}")

def parse_externalstress(stress_str):
    # scalar
    try:
        val = float(stress_str)
        return val
    except ValueError:
        pass

    # tuple / list / matrix
    try:
        arr = np.array(ast.literal_eval(stress_str), dtype=float)

        if arr.shape in [(3,), (6,), (3, 3)]:
            return arr
        else:
            raise ValueError
    except Exception:
        raise ValueError(
            "Invalid --externalstress format.\n"
            "Allowed formats:\n"
            "  0.0\n"
            "  'sx sy sz'\n"
            "  'sxx syy szz syz sxz sxy'\n"
            "  '[[sxx,sxy,sxz],[syx,syy,syz],[szx,szy,szz]]'"
        )

# =====================
# temperature funcs
# =====================
def update_temperature(dyn, total_step, ini_temperature, fin_temperature):
    temperature_interval = (fin_temperature - ini_temperature)/total_step
    new_temperature = ini_temperature + dyn.get_number_of_steps() * temperature_interval
    dyn.set_temperature(temperature_K = new_temperature)

def output_struct(structure):
    structure.write("POSCAR_final", format = "vasp")

def calc_polarization(structure, bec, ref_structure):
    volume = structure.get_volume()
    positions = structure.get_positions(wrap = True)
    frac_positions = structure.get_scaled_positions(wrap = True)
    ref_positions = ref_structure.get_positions(wrap = True)
    ref_frac_positions = ref_structure.get_scaled_positions(wrap = True)
    for i in range(len(frac_positions)):
        for j in range(3):
            delta = frac_positions[i, j] - ref_frac_positions[i, j]
            if delta > 0.5:
                frac_positions[i, j] -= 1
            elif delta < -0.5:
                frac_positions[i, j] += 1
    new_positions = frac_positions @ structure.get_cell()
    P = np.zeros(3)
    e_to_C = 1.602176634*1e-19
    A_to_cm = 1e-8
    for i, pos in enumerate(new_positions):
        Z = bec[i].reshape(3,3)
        P += np.dot(pos-ref_positions[i], Z)
    P /= volume
    P = P*e_to_C/(A_to_cm*A_to_cm) *1e6
    return P


# =====================
# electric field funcs
# =====================
def gradual_extforce_triangle(dyn, struct, model, Emax, total_step, positive_first=True, efield_direction = "z", BEC_update_interval = 10, ref = None, traj_interval = 1000, device = "cuda", use_MACE = True):
    step = dyn.get_number_of_steps()
    quarter = total_step // 4
    rate = Emax/quarter

    if positive_first:
        if step <= quarter:
            E = step * rate
        elif step <= 3 * quarter:
            E = quarter * rate - (step - quarter) * rate
        else:
            E = -quarter * rate + (step - 3 * quarter) * rate
    else:
        if step <= quarter:
            E = -step * rate
        elif step <= 3 * quarter:
            E = -quarter * rate + (step - quarter) * rate
        else:
            E = quarter * rate - (step - 3 * quarter) * rate
    if efield_direction == "x":
        E_field = np.array([E, 0, 0])
    elif efield_direction == "y":
        E_field = np.array([0, E, 0])
    elif efield_direction == "z":
        E_field = np.array([0, 0, E])
    elif efield_direction == "xy":
        vec = np.array([1, 1, 0])
        E_field = E * vec / np.linalg.norm(vec)
    elif efield_direction == "xz":
        vec = np.array([1, 0, 1])
        E_field = E * vec / np.linalg.norm(vec)
    elif efield_direction == "yz":
        vec = np.array([0, 1, 1])
        E_field = E * vec / np.linalg.norm(vec)
    elif efield_direction == "xyz":
        vec = np.array([1, 1, 1])
        E_field = E * vec / np.linalg.norm(vec)
    else:
        raise NotImplementedError(f"Electric field direction: {efield_direction} is not implemented yet")

    if (step-1) % BEC_update_interval == 0:
        global out
        if use_MACE:
            bec_struct = struct.copy()
            bec_struct.calc = model
            bec_struct.get_potential_energy()
            out = bec_struct.calc.results["becs"]
            del bec_struct
        else:
            out = Calculate(
                struct, model,
                graph_max_radius=3.0,
                num_radial=32,
                edge_sh_lmax=2,
                radial_basis=None,
                device=device
            )
    if ref and step == 1:
        with open("P-E_traj.dat", "w") as f:
            f.write("# step  E(V/Ang)  Px Py Pz (uC/cm^2)\n")
    if ref and step % traj_interval==0:
        P = calc_polarization(struct, out, ref)
        Px, Py, Pz = P
        with open("P-E_traj.dat", "a") as f:
            f.write(f"{step:8d} {E:15.8e} {Px:15.8e} {Py:15.8e} {Pz:15.8e}\n")

    elec_forces = np.array([
        np.dot(out[n].reshape(3, 3), E_field)
        for n in range(len(struct))
    ])

    dyn.set_extforce(elec_forces)
    #print(out[0])


def update_extforce(dyn, struct, model, total_step, E_field_list, efield_direction = "z", BEC_update_interval = 10, ref = None, traj_interval = 1000, device = "cuda", use_MACE = True):
    step = dyn.get_number_of_steps()
    interval = total_step/len(E_field_list)
    i = int((step - 1) // interval)

    if i >= len(E_field_list):
        dyn.set_extforce(np.zeros((len(struct), 3)))
        return

    E = E_field_list[i]
    if efield_direction == "x":
        E_field = np.array([E, 0, 0])
    elif efield_direction == "y":
        E_field = np.array([0, E, 0])
    elif efield_direction == "z":
        E_field = np.array([0, 0, E])
    elif efield_direction == "xy":
        E_field = np.array([E, E, 0])
    elif efield_direction == "xz":
        E_field = np.array([E, 0, E])
    elif efield_direction == "yz":
        E_field = np.array([0, E, E])
    elif efield_direction == "xyz":
        E_field = np.array([E, E, E])
    else:
        raise NotImplementedError(f"Electric field direction: {efield_direction} is not implemented yet")
    
    
    
    if (step-1) % BEC_update_interval ==0:
        global out
        if use_MACE:
            bec_struct = struct.copy()
            bec_struct.calc = model
            bec_struct.get_potential_energy()
            out = bec_struct.calc.results["becs"]
            del bec_struct
        else:
            out = Calculate(
                struct, model,
                graph_max_radius=3.0,
                num_radial=32,
                edge_sh_lmax=2,
                radial_basis=None,
                device=device
            )
        
    if ref and step == 1:
        with open("P-E_traj.dat", "w") as f:
            f.write("# step  E(V/Ang)  Px Py Pz (uC/cm^2)\n")
    if ref and step % traj_interval==0:
        P = calc_polarization(struct, out, ref)
        Px, Py, Pz = P
        with open("P-E_traj.dat", "a") as f:
            f.write(f"{step:8d} {E:15.8e} {Px:15.8e} {Py:15.8e} {Pz:15.8e}\n")

    elec_forces = np.array([
        np.dot(out[n].reshape(3, 3), E_field)
        for n in range(len(struct))
    ])

    dyn.set_extforce(elec_forces)


# =====================
# main
# =====================
def main():
    args = parse_args()
    
    #torch.cuda.set_per_process_memory_fraction(0.5, device=0)
    
    struct = ase.io.read(args.input)
    struct.set_constraint(FixCom())
    ref_struct = None
    if args.ref:
        ref_struct = ase.io.read(args.ref)

    else:
        print("No reference structure is set, so the polarization will not be calculated.")


    macemp = MACECalculator(
        model_paths=args.MLP_model,
        device=args.device, 
        enable_cueq=True,
        default_dtype="float32",
    )
    print(macemp)
    struct.calc = macemp
    if args.BEC_model:
        if args.use_Equivar == False:
            model = MACECalculator(
                model_paths=args.BEC_model,
                device=args.device, 
                model_type = "MACEField",
                default_dtype="float32",
                enable_cueq=True,
                compute_forces=False,
                compute_energy = False,
            )
            
            #model = macemp
            use_MACE = True
        else:
            from equivar_eval.scripts.calculate import Calculate
            model = torch.jit.load(
                args.BEC_model,
                map_location=args.device
            )
            model.eval()
            use_MACE = False

    MaxwellBoltzmannDistribution(struct, temperature_K=args.ini_temperature)
    timestep = args.timestep * units.fs

    if args.ensemble_type == "NPT":
        ttime = args.ttime * units.fs
        ptime = args.ptime * units.fs
        pfactor = (2/3) * units.kB * args.ini_temperature * args.N * ptime**2
        dyn = NPT(
            struct,
            timestep = timestep,
            temperature_K = args.ini_temperature,
            externalstress = parse_externalstress(args.externalstress),
            ttime=ttime,
            pfactor=pfactor,
            mask = parse_mask(args.mask)
        )
    elif args.ensemble_type == "Langevin":
        dyn = Langevin(
            struct,
            timestep = timestep,
            temperature_K=args.ini_temperature,
            friction=args.friction,
        )
    
    elif args.ensemble_type == "NVTBerendsen":
        dyn = NVTBerendsen(
            struct,
            timestep = timestep,
            temperature_K=args.ini_temperature,
            taut = args.taut*units.fs
        )

    if args.fin_temperature:
        dyn.attach(lambda:update_temperature(dyn, args.total_step, args.ini_temperature, args.fin_temperature), interval=1)
    traj = Trajectory("traj.traj", "w", struct)
    dyn.attach(traj.write, interval=args.traj_interval)
    dyn.attach(MDLogger(dyn, struct, "log_every_1000.log"), interval=args.traj_interval)
    dyn.attach(lambda: output_struct(struct), interval = 1)

    # ===== electric field attach =====
    if args.efield_mode == "triangle" and args.Emax > 0:
        run_steps = args.total_step
        dyn.attach(
            lambda: gradual_extforce_triangle(
                dyn, struct, model,
                Emax=args.Emax,
                total_step=run_steps,
                positive_first=args.positive_first,
                efield_direction = args.efield_direction, 
                BEC_update_interval = args.bec_update_interval,
                ref = ref_struct, 
                traj_interval = args.traj_interval,
                device = args.device, 
                use_MACE = use_MACE
            ),
            interval=1
        )
        rate = args.Emax/(args.total_step // 4)
        print(f"The triangular-wave electric field is set with the maximum field of {args.Emax} V/Å and the rate of {rate} V/(Å*step).")

    elif args.efield_mode == "step":
        dyn.attach(
            lambda: update_extforce(
                dyn, struct, model,
                E_field_list = args.Elist, total_step=args.total_step,
                efield_direction = args.efield_direction, 
                BEC_update_interval = args.bec_update_interval,
                ref = ref_struct,
                traj_interval = args.traj_interval,
                device = args.device,
                use_MACE = use_MACE
            ),
            interval=1
        )
        run_steps = args.total_step
        interval = args.total_step/len(args.Elist)
        print(f"The sequence of electric field {args.Elist} V/Å is set with the interval of {interval} steps.")

    else:
        # no electric field
        run_steps = args.total_step

    print(f"MD start: {datetime.datetime.now()}")
    dyn.run(run_steps)
    print(f"MD finished: {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
