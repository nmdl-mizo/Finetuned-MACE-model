# Finetuned MACE model
This model is the BTO finetuned MACE model that can be applied to bulk and defect-containing BTO systems. To use the models please install the MACE code.

## Example
In this example, the energy of a BTO crystal is calculated by BTO finetuned MACE model and Atomic Simulation Environment (ASE).
```
from ase.io import read
from mace.calculators import MACECalculator

bto = read('/example/BaTiO3_cubic.cif')
calculator = MACECalculator(model_path='/path-to-finetuned-mace-model/BTO_MACE.model', device='cpu')
bto.calc = calculator 

bto_energy = bto.get_potential_energy()
print("energy of BTO:", bto_energy)
```
## Author
* [Poyen Chen](https://github.com/poyeChen)
* [Mizoguchi Lab.](https://github.com/nmdl-mizo)

## License
The source code is licensed MIT.
