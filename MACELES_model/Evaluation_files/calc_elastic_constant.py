from ase.io import read
import ase.units as units
import numpy as np
import matplotlib.pyplot as plt
from mace.calculators import mace_mp
from ase.constraints import UnitCellFilter
from ase.optimize import BFGS
from pymatgen.analysis.eos import EOS
from pymatgen.analysis.elasticity.strain import Deformation
from pymatgen.analysis.elasticity.elastic import ElasticTensor

structure = read("/home/poyen/BTO_MLFF/tetragonal/structurerelaxation_PS/CONTCAR")
calc =  mace_mp(model="/home/poyen/BTO_MLFF/MACE/MACE_large_100.model", device='cuda')
#calc =  mace_mp(model="/home/poyen/BTO_MLFF/MACE/LES_model/test/MACE_BTO.model", device='cuda')
structure.calc = calc
ucf = UnitCellFilter(structure)
opt = BFGS(ucf)
opt.run(fmax=0.01)
print("Optimized lattice constants:", structure.get_cell_lengths_and_angles())

scale_factors = np.linspace(0.96, 1.03, 5)
volumes = []
energies = []

for f in scale_factors:
    atoms_scaled = structure.copy()
    atoms_scaled.set_cell(structure.cell * f, scale_atoms=True)
    volumes.append(atoms_scaled.get_volume())
    # MD/能量計算
    atoms_scaled.calc = calc
    opt = BFGS(atoms_scaled)
    opt.run(fmax=0.01)
    energy = atoms_scaled.get_potential_energy()
    energies.append(energy)
eos = EOS()
eos_fit = eos.fit(volumes = volumes, energies = energies)
print(eos_fit)
V0 = eos_fit.v0
E0 = eos_fit.e0
B0 = eos_fit.b0
B0_GPa = eos_fit.b0_GPa
print("V0:", V0, "E0:", E0, "B0:", B0, "B0_GPa':", B0_GPa)


# 假設已經得到一組 epsilon -> sigma

strain_values = [0.015, -0.015]
strain_list = []
for val in strain_values:
    # Voigt 6 分量: [xx, yy, zz, yz, xz, xy]
    strain_list.extend([
        [val, 0, 0, 0, 0, 0],
        [0, val, 0, 0, 0, 0],
        [0, 0, val, 0, 0, 0],
        [0, 0, 0, val, 0, 0],
        [0, 0, 0, 0, val, 0],
        [0, 0, 0, 0, 0, val]
    ])

# =========================
# 4️⃣ 對每個應變計算應力
# =========================
stress_list = []
applied_strains = []

def voigt_to_matrix(eps_voigt):
    """
    Convert Voigt 6-component strain to 3x3 matrix
    eps_voigt = [εxx, εyy, εzz, εyz, εxz, εxy]
    """
    return np.array([
        [eps_voigt[0], eps_voigt[5], eps_voigt[4]],
        [eps_voigt[5], eps_voigt[1], eps_voigt[3]],
        [eps_voigt[4], eps_voigt[3], eps_voigt[2]]
    ])

def voigt6_to_matrix(stress_voigt):
    return np.array([
        [stress_voigt[0], stress_voigt[5], stress_voigt[4]],
        [stress_voigt[5], stress_voigt[1], stress_voigt[3]],
        [stress_voigt[4], stress_voigt[3], stress_voigt[2]]
    ])

for eps in strain_list:
    # 建立應變後結構
    strain_matrix = voigt_to_matrix(eps)
    atoms_strained = structure.copy()
    atoms_strained.set_cell(structure.cell @ (np.eye(3) + strain_matrix), scale_atoms=True)
    atoms_strained.calc = calc
    opt = BFGS(atoms_strained)
    opt.run(fmax=0.05)
    # ASE get_stress 默認返回 6 分量 Voigt
    stress = atoms_strained.get_stress(voigt=True)  # eV/Å^3
    stress_list.append(stress)
    applied_strains.append(eps)

#print(stress_list, applied_strains)
stress_array = np.array(stress_list)
strain_array = np.array(applied_strains)
stress_matrices = np.array([voigt6_to_matrix(s) for s in stress_array])
strain_matrices = np.array([voigt6_to_matrix(s) for s in strain_array])
# =========================
# 5️⃣ 擬合彈性張量
# =========================
C = ElasticTensor.from_diff_fit(strain_matrices, stress_matrices)
#C = ElasticTensor.from_diff_fit(strain_array, stress_array)
print("Elastic tensor Cij (GPa):")
print(C.voigt* 160.21766208)