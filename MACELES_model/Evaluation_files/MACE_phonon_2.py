from ase.phonons import Phonons
from ase.io import read
from mace.calculators import MACECalculator, mace_mp
from pymatgen.core import Structure
from pymatgen.symmetry.bandstructure import HighSymmKpath
from ase.dft.kpoints import get_bandpath
from pymatgen.io.vasp import Poscar
from pymatgen.symmetry.bandstructure import HighSymmKpath
from pymatgen.io.vasp.inputs import Kpoints
import numpy as np


atoms = read('POSCAR_primitive')
calc_1 = mace_mp(model="../../BTO_MACE.model", device='cuda')
calc_2 = mace_mp(model='../../BTO_MACELES.model', device='cuda')  # 使用finetuned模型的计算器
supercell_size = (3, 3, 3)
ph_1 = Phonons(atoms, calc_1, supercell=supercell_size)
ph_1.run()
ph_1.read(acoustic=True)
ph_1.clean()
path_1 = atoms.cell.bandpath(npoints=101) 
bs_1 = ph_1.get_band_structure(path_1, modes = False, born = False)

ph_2 = Phonons(atoms, calc_2, supercell=supercell_size)
ph_2.run()
ph_2.read(acoustic=True)
ph_2.clean()
path_2 = atoms.cell.bandpath(npoints=101) 
bs_2 = ph_2.get_band_structure(path_2, modes = False, born = False)



import matplotlib.pyplot as plt  # noqa

xcoords_1, _1, _2 =bs_1.get_labels()
#print(_1)
#print(_2)
bs_energies_1 = bs_1.energies
for spin, e_kn in enumerate(bs_energies_1):
    f = e_kn[:,0] *241.8
    for e_k in e_kn.T[1:]:
        f = e_k*241.8

xcoords_2, _1, _2 =bs_2.get_labels()
#print(_1)
#print(_2)
bs_energies_2 = bs_2.energies
for spin, e_kn in enumerate(bs_energies_2):
    f = e_kn[:,0] *241.8
    for e_k in e_kn.T[1:]:
        f = e_k*241.8



struct = Poscar.from_file("/POSCAR_primitive").structure
kpath = HighSymmKpath(struct)
kpts = Kpoints.automatic_linemode(divisions = 40, ibz = kpath)

path = [[kpts.labels[2*l], kpts.labels[2*l+1]] for l in range(int(len(kpts.labels)/2))] 
new_list = []
n_list = 0
list_position = [0]
for p in range(len(path)-1):
    if p ==0:
        new_list.append(path[p][0])
    if path[p][1] == path[p+1][0]:
        new_list.append(path[p][1])
    elif path[p][1] != path[p+1][0]:
        new_list.append(path[p][1]+"|"+path[p+1][0])
        n_list +=1
        list_position.append(p+1)
    if p+1 == len(path)-1:
        new_list.append(path[p+1][1])
list_position.append(len(path))

for n in range(len(new_list)):
    if new_list[n] =="\\Gamma":
        new_list[n] ="$\Gamma$"

with open("./band_NAC.dat", "r") as PS_file:
    PS_x_1 = []
    PS_y_1 = []
    PS_x_n = []
    PS_y_n = []
    PS_n = 0
    for line in PS_file:
        if PS_n == 1:
            ln = " ".join(line.split()).split()
            endpoint = ln[1:]
        if line.isspace():
            if PS_x_n !=[]:
                PS_x_1.append(PS_x_n)
                PS_y_1.append(PS_y_n)
                PS_x_n = []
                PS_y_n = []

        elif PS_n > 1 and not line.isspace():
            ln = " ".join(line.split()).split()
            PS_x_n.append(float(ln[0]))
            PS_y_n.append(float(ln[1]))
        PS_n+=1

print(np.shape(PS_x_1), np.shape(PS_y_1))

with open("./band.dat", "r") as PS_file:
    PS_x_2 = []
    PS_y_2 = []
    PS_x_n = []
    PS_y_n = []
    PS_n = 0
    for line in PS_file:
        if PS_n == 1:
            ln = " ".join(line.split()).split()
            endpoint = ln[1:]
        if line.isspace():
            if PS_x_n !=[]:
                PS_x_2.append(PS_x_n)
                PS_y_2.append(PS_y_n)
                PS_x_n = []
                PS_y_n = []

        elif PS_n > 1 and not line.isspace():
            ln = " ".join(line.split()).split()
            PS_x_n.append(float(ln[0]))
            PS_y_n.append(float(ln[1]))
        PS_n+=1

endpoint = np.array([float(l) for l in endpoint])

import matplotlib.pyplot as plt

plt.Figure(dpi = 300)
for i in range(len(PS_x_1)):
    if i == 0:
        plt.plot(PS_x_2[i], PS_y_2[i], color = "black", label = "DFT without LO_TO", linestyle = "--")
        plt.plot(PS_x_1[i], PS_y_1[i], color = "green", label = "DFT with LO_TO", linestyle = "--")
    else:
        plt.plot(PS_x_2[i], PS_y_2[i], color = "black", linestyle = "--")
        plt.plot(PS_x_1[i], PS_y_1[i], color = "green", linestyle = "--")

for n in range(len(endpoint)):
    plt.axvline(x = endpoint[n], color = "black", linestyle = "--")

for spin, e_kn in enumerate(bs_energies_1):
    f = e_kn[:,0] *241.8
    plt.plot(xcoords_1/max(xcoords_1)*endpoint[-1], f, color = "orange", label="MACE")
    for e_k in e_kn.T[1:]:
        f = e_k*241.8
        plt.plot(xcoords_1/max(xcoords_1)*endpoint[-1], f, color = "orange")

for spin, e_kn in enumerate(bs_energies_2):
    f = e_kn[:,0] *241.8
    plt.plot(xcoords_2/max(xcoords_2)*endpoint[-1], f, color = "blue", label="MACELES")
    for e_k in e_kn.T[1:]:
        f = e_k*241.8
        plt.plot(xcoords_2/max(xcoords_2)*endpoint[-1], f, color = "blue")
plt.xticks(endpoint, new_list, fontsize = 12)
plt.yticks(fontsize = 12)
plt.xlim(endpoint[0], endpoint[-1]))
plt.ylabel("Frequency (THz)", fontsize = 14)
plt.tight_layout()
plt.savefig('phonon_MACELES_comparison_333.png')
