from tests.test_files.test_read_gjf import _test_read_gjf
from tests.test_files.test_read_ints import _test_ints
from tests.test_files.test_read_wfn import _test_read_wfn, _test_molecular_orbitals, MolecularOrbital
from tests.test_files.test_read_aim import _test_read_aim
from tests.test_files.test_read_gau import _test_read_gau, _assert_atomic_forces
from tests.test_atoms import _test_atoms_coords

from pathlib import Path
from typing import Dict, Optional, List
from ichor.core.files import PointDirectory
from ichor.core.files.aimall.aim import AimAtom
from ichor.core.common.types import Version
from ichor.core.common.types.itypes import T
from tests.path import get_cwd
from tests.test_files import _assert_val_optional
from ichor.core.atoms import Atoms, Atom

from ichor.core.files.gaussian.gaussian_out import AtomForce, MolecularDipole, MolecularHexadecapole, MolecularOctapole, MolecularQuadrupole, TracelessMolecularQuadrupole
from ichor.core.files.gaussian.wfn import MolecularOrbital
from ichor.core.common.units import AtomicDistance
import numpy as np

from ichor.core.files.aimall.int import (
    CriticalPoint,
    CriticalPointType,
)

from ichor.core.atoms import ALF
from ichor.core.files import XYZ

example_dir = get_cwd(__file__) / "example_points_directory" / "water_monomer_points_dir"

def _test_point_directory(
    point_dir_path = Path,
    #######
    # Gaussian Tests
    ########
    # Gaussian .gjf test
    gjf_link0: Optional[List[str]] = None,
    gjf_method: Optional[str] = None,
    gjf_basis_set: Optional[str] = None,
    gjf_keywords: Optional[List[str]] = None,
    gjf_title: Optional[str] = None,
    gjf_charge: Optional[int] = None,
    gjf_spin_multiplicity: Optional[int] = None,
    gjf_atoms: Optional[Atoms] = None,
    # .gau/.log Gaussian output file
    gau_forces: Dict[str, AtomForce] = None,
    gau_charge: int = None,
    gau_multiplicity: int = None,
    gau_atoms: Atoms = None,
    gau_molecular_dipole: MolecularDipole = None,
    gau_molecular_quadrupole: MolecularQuadrupole = None,
    gau_traceless_molecular_quadrupole: TracelessMolecularQuadrupole = None,
    gau_molecular_octapole: MolecularOctapole = None,
    gau_molecular_hexadecapole: MolecularHexadecapole = None,
    # .wfn Gaussian wavefunction file
    wfn_method: str = None,
    wfn_atoms: Atoms = None,
    wfn_title: str = None,
    wfn_program: str = None,
    wfn_n_orbitals: int = None,
    wfn_n_primitives: int = None,
    wfn_n_nuclei: int = None,
    wfn_centre_assignments: List[int] = None,
    wfn_type_assignments: List[int] = None,
    wfn_primitive_exponents: np.ndarray = None,
    wfn_molecular_orbitals: List[MolecularOrbital] = None,
    wfn_total_energy: float = None,
    wfn_virial_ratio: float = None,
    
    #####
    #INTs Directory
    #####
    ints_atom_name: List[str] = None,
    ints_atom_num: Dict[str, int] = None,
    ints_title: Dict[str, str] = None,
    ints_dft_model: Dict[str, str] = None,
    ints_basin_integration_results: Dict[str, Dict[str, float]] = None,
    ints_integration_error: Dict[str, float] = None,
    ints_critical_points: Dict[str, List[CriticalPoint]] = None,
    ints_bond_critical_points: Dict[str, List[CriticalPoint]] = None,
    ints_ring_critical_points: Dict[str, List[CriticalPoint]] = None,
    ints_cage_critical_points: Dict[str, List[CriticalPoint]] = None,
    ints_properties: Dict[str, Dict[str, float]] = None,
    ints_net_charge: Dict[str, float] = None,
    ints_global_spherical_multipoles: Dict[str, Dict[str, float]] = None,
    ints_local_spherical_multipoles: Dict[str, Dict[str, float]] = None,
    ints_C_matrix_dict: Dict[str, np.ndarray] = None,
    ints_iqa_energy_components: Dict[str, Dict[str, float]] = None,
    ints_iqa: Dict[str, float] = None,
    ints_e_intra: Dict[str, float] = None,
    ints_q: Dict[str, float] = None,
    ints_q00: Dict[str, float] = None,
    ints_dipole_mag: Dict[str, float] = None,
    ints_total_time: Dict[str, int] = None
    ):
    
    point_dir_inst = PointDirectory(point_dir_path)

    gjf_path = point_dir_inst.gjf.path
    gaussian_out_path = point_dir_inst.gaussian_out.path
    xyz_path = point_dir_inst.xyz.path
    ints_path = point_dir_inst.ints.path
    aim_path = point_dir_inst.aim.path
    
    _test_read_gjf(
        gjf_path = gjf_path,
        link0 = gjf_link0,
        method = gjf_method,
        basis_set = gjf_basis_set,
        keywords = gjf_keywords,
        title = gjf_title,
        charge = gjf_charge,
        spin_multiplicity = gjf_spin_multiplicity,
        atoms = gjf_atoms)
    
    _test_read_gau(
        gau_path = gaussian_out_path,
        forces = gau_forces,
        charge = gau_charge,
        multiplicity = gau_multiplicity,
        atoms = gau_atoms,
        molecular_dipole = gau_molecular_dipole,
        molecular_quadrupole = gau_molecular_quadrupole,
        traceless_molecular_quadrupole = gau_traceless_molecular_quadrupole,
        molecular_octapole = gau_molecular_octapole,
        molecular_hexadecapole = gau_molecular_hexadecapole,
    )

    _test_read_wfn(
        method = wfn_method,
        atoms = wfn_atoms,
        title = wfn_title,
        program = wfn_program,
        n_orbitals = wfn_n_orbitals,
        n_primitives = wfn_n_primitives,
        n_nuclei = wfn_n_nuclei,
        centre_assignments= wfn_centre_assignments,
        type_assignments = wfn_type_assignments,
        primitive_exponents = wfn_primitive_exponents,
        molecular_orbitals = wfn_molecular_orbitals,
        total_energy = wfn_total_energy,
        virial_ratio = wfn_virial_ratio,
    )
    
    _test_ints(
        atom_name = ints_atom_name,
        atom_num = ints_atom_num,
        title = ints_title,
        dft_model = ints_dft_model,
        basin_integration_results = ints_basin_integration_results,
        integration_error = ints_integration_error,
        critical_points = ints_critical_points,
        bond_critical_points = ints_bond_critical_points,
        ring_critical_points = ints_ring_critical_points,
        cage_critical_points = ints_cage_critical_points,
        properties = ints_properties,
        net_charge = ints_net_charge,
        global_spherical_multipoles = ints_global_spherical_multipoles,
        local_spherical_multipoles = ints_local_spherical_multipoles,
        C_matrix_dict = ints_C_matrix_dict,
        iqa_energy_components = ints_iqa_energy_components,
        iqa = ints_iqa,
        e_intra = ints_e_intra,
        q = ints_q,
        q00 = ints_q00,
        dipole_mag = ints_dipole_mag,
        total_time = ints_total_time
        )
    

def test_water_monomer_point_directory1():
    
    reference_gjf_atoms = Atoms(
        [Atom("O", -0.03348733, -0.46689766, -0.00424905),
         Atom("H", -0.50428226, 0.20263196, 0.56694849),
         Atom("H", 0.53776959, 0.26426570, -0.56269944)],
    )
    
    reference_gau_atoms = Atoms(
        [Atom("O", -0.03349000, -0.46690000, -0.00425000),
         Atom("H", -0.50428000, 0.20263000, 0.56695000),
         Atom("H", 0.53777000, 0.26427000, -0.56270000)]
    )
    
    reference_wfn_atoms = Atoms(
        [Atom("O", -0.06328188, -0.88230871, -0.00802954, units=AtomicDistance.Bohr), 
        Atom("H", -0.95295537, 0.38291891, 1.07137738, units=AtomicDistance.Bohr),
        Atom("H", 1.01623725, 0.49938980, -1.06334784, units=AtomicDistance.Bohr)]
    )
    
    wfn_expected_molecular_orbitals = [
        MolecularOrbital(1, 0.0, 2.0, -19.154182, [0.49669426, 0.92575644, 1.5697501, 2.3756499, 2.963436, 2.543069, 0.97386032, 3.5843855e-05, 0.00038458104, 0.0014176381, 0.0041450907, 0.0049950359, -0.0060170501, 0.055564088, -4.03979e-05, -0.00012364374, 0.00053080754, 0.00051470476, 0.00034721679, 0.0074891282, 0.0072619352, 0.0048988586, 7.5052246e-05, 7.2775432e-05, 4.9093877e-05, -0.00072771178, -0.00076146816, 0.00072621562, -0.00030466521, -0.00037314629, 0.00029929949, -1.0974244e-05, -5.2155588e-06, 1.149832e-05, -0.0004049188, 0.0004919329, -8.7014098e-05, -0.00031387801, -0.0031862954, 0.0007512178, 4.6711379e-05, 
                            -7.5787556e-05, 2.9076177e-05, -0.00066251538, 0.00083657467, 0.00062864363, 1.2829503e-05, -2.0106943e-05, 7.2774406e-06, -7.4705395e-05, 0.00013270782, 6.4474751e-05, 0.00026561335, -0.00010236276, -0.00024245916, -0.00058934746, 9.3219056e-06, 2.9797914e-05, -0.0002074926, 0.00029776638, 0.00069757957, -0.001223812, 3.8822578e-06, 8.3669458e-05, -1.4025414e-05, -3.6218188e-05, -9.1828363e-05, 3.3924706e-05, 2.4571415e-05, -0.00015918001, 8.1515372e-06, 0.00085355854, 0.00017231581, 0.00031077865, 0.00045824294, -0.00011492119, -0.00028645356, -6.2492059e-06, 2.6454351e-05, -0.00012503814, -3.9724128e-05, -0.00022800946, 0.00020695578, 0.00026640426, -4.6291049e-05, 4.2369526e-05, 5.4116838e-05, 0.00018803338, -0.00015599909, -3.2034295e-05, 0.001340348, 0.0011287606, -0.0016009731, -5.4060485e-06, 1.6384663e-05, -1.0978615e-05, 1.9015956e-05, 4.5805872e-05, -2.0446424e-05, 8.0188639e-05, 0.00014462351, 0.00021324729, 0.0013831988, 0.0003270961, 1.4980556e-05, -0.0005125854, -0.00077665514, 0.00049057516, -0.00045437844, -0.00060409094, 0.00044223154, -3.5639775e-05, -3.067183e-05, 3.6144561e-05, -3.7252232e-05, 6.8969239e-05, -3.1717007e-05, 0.00010388175, -0.00015483464, -8.1498041e-05, -6.8556676e-06, 1.4122111e-05, -7.266443e-06, 
                            4.1521315e-05, -3.4261392e-05, -3.853334e-05]),
        MolecularOrbital(2, 0.0, 2.0, -0.996981, [-0.10560755, -0.19683511, -0.33376158, -0.50511266, -0.63008823, -0.54070945, -0.20706299, -0.001640198, -0.017598248, -0.064870455, -0.18967741, -0.2285705, 0.27533738, 0.15615859, 0.073647452, 0.0034072834, -0.01834959, -0.01779293, -0.012003006, 0.29148507, 0.28264247, 0.19066894, 0.045412179, 0.044034538, 0.029705439, -0.002046197, 0.070451497, 0.0083738396, 0.00040357462, 0.0054919929, 3.9027127e-05, -1.2703256e-06, 0.00012652028, 1.2375888e-05, -0.0081544755, 0.012481801, -0.0043273251, -0.0031385919, -0.038132938, 0.010051027, -0.0026132879, 0.0043806164, -0.0017673285, 0.0017041335, -0.010572908, 0.00022258483, -6.3656373e-05, 0.00015580875, -9.215238e-05, 0.00025668679, 8.703928e-05, -0.00024670341, -3.6141016e-05, -0.0010958287, 0.00017080213, 0.00096108015, 0.00068245871, -0.00092957396, -0.0008526571, 0.0026050275, 0.00041716759, -0.023092346, -0.0001457759, 0.00021805406, 0.00011818876, 0.00047792749, -0.00032352298, -4.2821168e-05, -4.0599786e-05, -0.00033063921, -0.0003117451, -0.0010656986, 0.023750114, 0.042834309, 0.063159164, 0.023884032, -0.0011687185, -7.9089539e-05, 0.014318736, -0.017879314, -0.01715598, 0.0025575411, -0.0031489416, -0.0030597217, -0.0001710597, 0.00023430421, 0.00020688467, -0.00084469629, 0.00073048617, 0.00011421012, -0.0056133942, -0.0051385534, 0.0067612022, 8.5325022e-06, -2.0263723e-05, 1.1731221e-05, 1.2567027e-05, -5.4067756e-05, -1.3947825e-05, 0.018766469, 0.033846099, 0.049906053, 0.018098847, -0.00078260356, -4.322687e-05, -0.011984024, -0.01315612, 0.011905548, -0.0021873161, -0.0024949538, 0.002165596, 0.00011453074, 0.00014990723, -0.0001115987, -0.00019405214, 0.0003973352, -0.00020328306, 0.0034280977, -0.0031996384, -0.0033506365, -2.8512305e-05, 5.5955541e-05, -2.7443236e-05, 0.00016213018, -0.00016106568, -0.00014760206]),
        MolecularOrbital(3, 0.0, 2.0, -0.494315, [0.0049777445, 0.0092776973, 0.01573164, 0.023808164, 0.029698807, 0.025485995, 0.0097597822, 9.0278366e-05, 0.00096862762, 0.0035705438, 0.010440061, 0.012580781, -0.015154884, -0.007432128, -0.013487826, -0.0013599314, -0.98681099, -0.95687471, -0.64550203, 0.1027757, 0.099657857, 0.067228602, 1.0838147, 1.0509357, 0.70895502, -0.21472322, 0.017487143, 0.23540532, -0.026752436, 0.00025823135, 0.029161969, -0.00044967704, 9.0099281e-06, 0.00049061414, -0.0045187299, 0.00082546727, 0.0036932626, -0.087402212, -0.0061353495, 0.096012348, -0.00075816477, 0.00014904744, 0.00060911732, -0.017359926, 0.0017287175, 0.018807598, 5.8677436e-05, -0.00010309986, 4.4422423e-05, -0.00037445431, 0.00051180986, 0.00033627623, 0.0052766077, 0.00041925137, -0.0043452796, -0.0028248729, -0.0018784994, 0.0099169406, -0.01300495, 0.00062074533, 0.0031188982, 0.0022529255, 0.00053520519, 0.00016262331, -0.00050487352, -0.00093536991, -0.00036389508, 0.00051414341, -0.00067024565, -0.00012397484, 0.0010004771, 0.0012117218, 0.036111652, 0.065128851, 0.096032453, 
                            0.065657156, 0.008191008, -0.00017886164, 0.0077385905, -0.025809185, -0.010679957, 0.0033187913, -0.011063693, -0.004579657, -0.00026968425, -0.00026102765, 0.0002708626, -0.0034881743, 0.0054518001, -0.0019636258, -0.010233695, -0.0063319213, 0.013142272, -0.00016347722, 0.00030032566, -0.00013684843, -0.00041932318, 0.00015032844, 0.00052305275, -0.032870422, -0.059283159, -0.087412984, -0.054932325, -0.0075825906, 0.00021126276, 0.0068225402, 0.020609735, -0.0056336192, 0.0023892465, 0.0089005918, -0.0018277968, -0.00017098057, 0.00034660061, 0.00021645383, 0.0021322149, -0.0046432152, 0.0025110003, -0.008252086, 0.0032361612, 0.0074894949, 0.00013279753, -0.00031413729, 0.00018133976, -0.00074591166, 0.00014577358, 0.00071735346]),
        MolecularOrbital(4, 0.0, 2.0, -0.413209, [0.037978667, 0.070785991, 0.1200276, 0.181649, 0.22659281, 0.19445034, 0.074464152, 0.00063391986, 0.0068015441, 0.025071772, 0.073308391, 0.088340176, -0.1064151, -0.063247858, -0.073634294, -0.011454607, 0.11537788, 0.11187773, 0.075472056, 1.5256706, 1.4793873, 0.99798594, 0.0074353994, 0.0072098363, 0.004863713, 0.027752383, 0.33247628, -0.0012214373, 0.0046837308, 0.045554597, -0.001128402, 8.6120462e-05, 0.00096901264, 
                            -9.5393121e-06, -0.020887921, 0.039617078, -0.018729156, 0.0075846139, -0.026505313, 0.0044730474, -0.0057204894, 0.011737944, -0.0060174542, 0.0032747996, 0.0016194092, -0.00062892936, -0.00011040063, 0.00032686804, -0.00021646741, 0.00040757628, 0.00082994676, -0.0004321772, -0.00090507084, 0.0032535025, 0.00037804171, 0.0024213243, -0.0057713098, -0.0024088941, 0.00029388819, -0.0039891976, 0.001274769, -0.024805085, -0.00016668145, 0.00069186245, 8.2680151e-05, 0.00055621766, -0.00098358696, 7.4149341e-06, -5.6173314e-05, -0.0010920004, -0.00025545539, 0.00015044422, 0.022008124, 0.039692559, 0.058526654, 0.048578695, 0.009784151, 0.00017014943, 0.012924857, 0.0030401609, -0.013812818, 0.0079305736, -0.00057537587, -0.0086869602, 0.00036465419, 0.00034333001, -0.00036641848, 0.00073562467, -0.0026741512, 0.0019385265, -0.004816781, -0.0090859131, 0.0053452576, 6.6338414e-05, -0.00018405616, 0.00011771774, -0.00011112896, -0.00049931694, 0.00011750396, 0.025545768, 0.046072845, 0.067934383, 0.05173125, 0.011858316, 0.00015664081, -0.0105704, 0.0010252089, 0.011602894, -0.0074233863, -0.0015257443, 0.0079547553, -0.00046809192, 0.00011720964, 0.00052082973, 0.00084258516, -0.0019922298, 0.0011496446, 0.003909221, -0.0075123494, -0.0041242671, 1.2341427e-05, -4.683084e-05, 3.4489413e-05, 0.00051248735, -0.00074520265, -0.00050444019]),
        MolecularOrbital(5, 0.0, 2.0, -0.323897, [-4.9573078e-07, -9.2396067e-07, -1.5667052e-06, -2.3710417e-06, -2.9576876e-06, -2.538136e-06, -9.7197124e-07, -4.7592968e-09, -5.1064132e-08, -1.88232e-07, -5.5037934e-07, -6.6323387e-07, 7.9893548e-07, 4.9013225e-07, 4.8900032e-06, -2.7749943e-07, 1.3187806, 1.2787736, 
                            0.8626531, -0.10563696, -0.10243231, -0.069100234, 1.2107629, 1.1740327, 0.79199552, 0.29695076, -0.023785257, 0.27262907, 0.051912095, -0.0041559418, 0.047662079, 0.0020162263, -0.00016160841, 0.0018512568, -0.00092031565, -0.0037260186, 0.0046463343, 0.04659864, 0.004216792, 0.042307861, 0.00040538728, -0.0011505339, 0.0007451466, 0.014333452, 0.0011830597, 0.013125284, 0.00013127732, -5.4610338e-05, -7.6666985e-05, 0.0006795092, 3.7287788e-05, 0.00064117531, 0.0019247304, -0.00074760585, 0.0034533362, 0.0092884686, 0.00036937401, -0.018736235, -0.01506266, 0.0018734435, 0.0083762266, 0.004490453, 9.2383053e-05, -5.9320761e-05, 0.00014655616, 0.00069929444, 0.0005369158, -0.0011525137, -0.0009764436, -0.00035895352, 0.0007128452, 0.000221971, -2.3915669e-07, -4.3132894e-07, -6.3599426e-07, -6.2829501e-06, 1.8964402e-06, 8.3724006e-10, 0.017103516, -0.0013692626, 0.015704172, 0.0085650858, -0.00068552466, 0.0078655465, 0.0010649959, -8.4852521e-05, 0.00097657123, 0.0049884686, 0.00054563671, -0.0055341053, -0.0072134755, -0.0014467624, -0.0057730897, 0.00047275682, 4.5155307e-05, -0.00051791213, -0.00060422903, -0.00013069904, -0.00047528094, -4.2086509e-07, -7.5904752e-07, -1.1192151e-06, -2.5100693e-06, -1.0334872e-06, 5.7045764e-09, 0.014183236, -0.0011354608, 0.013021715, 0.0072332084, -0.00057945081, 0.0066381132, 0.00088918263, -7.1094634e-05, 0.00081570384, -0.0049621795, 0.00047940724, 0.0044827722, -0.0055894235, 0.00032838963, -0.0058879042, -0.00038392027, 3.0630065e-05, 0.00035329021, -0.00035137257, 3.2662389e-05, -0.00038117806]),
        ]
    
    ints_critical_points = {"O1":
        [
            CriticalPoint(1, CriticalPointType.Bond, -0.76381542,  0.11484932,  0.84198109, ['H2']),
            CriticalPoint(2, CriticalPointType.Bond, 0.75472806,  0.16630947, -0.80755695, ['H3']),
        ]
        }
    
    water_monomer_alf = [ALF(0, 1, 2), ALF(1,0,2), ALF(2,0,1)]
    xyz_file_inst = XYZ(example_dir / "WATER_MONOMER0001" / "WATER_MONOMER0001.xyz")
    # calculate system alf and also calculate C matrices for all atoms
    C_matrices_dict = xyz_file_inst.C_matrix_dict(water_monomer_alf)
    
    _test_point_directory(
    point_dir_path = example_dir / "WATER_MONOMER0001",
    
    #######
    # Gaussian
    ########
    # .gjf
    gjf_link0 = ['nproc=2', 'mem=1GB'],
    gjf_method = 'B3LYP',
    gjf_basis_set = 'AUG-cc-pVTZ',
    gjf_keywords = ['SCRF=(Solvent=Water)', 'nosymm', 'output=wfn'],
    gjf_title = 'WATER_MONOMER0001',
    gjf_charge = 0,
    gjf_spin_multiplicity = 1,
    gjf_atoms = reference_gjf_atoms,
    # .gau Gaussian output
    forces = {},
    charge = 0,
    multiplicity = 1,
    atoms = reference_gau_atoms,
    molecular_dipole = MolecularDipole(x=0.1426, y=2.3942, z=0.0535, total=2.3991),
    molecular_quadrupole = MolecularQuadrupole(xx=-6.4806, yy=-7.7366, zz=-6.204, xy=0.0721, xz=-1.6772, yz=-0.0534),
    traceless_molecular_quadrupole = TracelessMolecularQuadrupole(xx=0.3265, yy=-0.9296, zz=0.6031, xy=0.0721, xz=-1.6772, yz=-0.0534),
    molecular_octapole = MolecularOctapole(xxx=0.5715, yyy=8.4307, zzz=0.1809, xyy=0.1988, xxy=3.0691, xxz=0.0434, xzz=0.1882, yzz=3.0845, yyz=0.0037, xyz=-0.1253),
    molecular_hexadecapole = MolecularHexadecapole(xxxx=-8.4442, yyyy=-15.1828, zzzz=-8.3154, xxxy=-0.284, xxxz=-0.1887, yyyx=-0.2953, yyyz=0.0517, zzzx=-0.264, zzzy=0.0379, xxyy=-3.8874, xxzz=-2.4725, yyzz=-3.8541, xxyz=-0.0366, yyxz=-0.1597, zzxy=-0.0788),
    # .wfn Gaussian wavefunction file
    method = "B3LYP",
    atoms = reference_wfn_atoms,
    title = 'WATER_MONOMER0001',
    program = 'GAUSSIAN',
    n_orbitals = 5,
    n_primitives = 126,
    n_nuclei = 3,
    centre_assignments= [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    type_assignments = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 2, 3, 4, 2, 3, 4, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 6, 7, 8, 9, 10, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 1, 1, 1, 1, 1, 1, 2, 3, 4, 2, 3, 4, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 6, 7, 8, 9, 10, 1, 1, 1, 
1, 1, 1, 2, 3, 4, 2, 3, 4, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 6, 7, 8, 9, 10],
    primitive_exponents = [15330.0, 2299.0, 522.4, 147.3, 47.55, 16.76, 6.207, 522.4, 147.3, 47.55, 16.76, 6.207, 0.6882, 1.752, 0.2384, 0.07376, 34.46, 7.749, 2.28, 34.46, 7.749, 2.28, 34.46, 7.749, 2.28, 0.7156, 0.7156, 0.7156, 0.214, 0.214, 0.214, 0.05974, 0.05974, 0.05974, 2.314, 2.314, 2.314, 2.314, 2.314, 2.314, 0.645, 0.645, 0.645, 0.645, 0.645, 0.645, 0.214, 0.214, 0.214, 0.214, 0.214, 0.214, 1.428, 1.428, 1.428, 1.428, 1.428, 1.428, 1.428, 1.428, 1.428, 1.428, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 33.87, 5.095, 1.159, 0.3258, 0.1027, 0.02526, 1.407, 1.407, 1.407, 0.388, 0.388, 0.388, 0.102, 0.102, 0.102, 1.057, 1.057, 1.057, 1.057, 1.057, 1.057, 0.247, 0.247, 0.247, 0.247, 0.247, 0.247, 33.87, 5.095, 1.159, 0.3258, 0.1027, 0.02526, 1.407, 1.407, 1.407, 0.388, 0.388, 0.388, 0.102, 0.102, 0.102, 1.057, 1.057, 1.057, 1.057, 1.057, 1.057, 0.247, 0.247, 0.247, 0.247, 0.247, 0.247],
    molecular_orbitals = wfn_expected_molecular_orbitals,
    total_energy = -76.460540818734,
    virial_ratio = 2.00902678,
    
    ######
    # INTs
    ######
    atom_name = {'O1': 'O1'},
    atom_num = {'O1': 1},
    title = {'O1': 'WATER_MONOMER0001'},
    dft_model = {'O1': 'Restricted B3LYP'},
    basin_integration_results = {'O1': {'N': 9.0762060817, 'G': 75.038982117, 'K': 75.03894204, 'L': -4.0077877571e-05, 'WeizKE': 56.664620514, 'TFKE': 68.244617363, 'I': 2.6389848033, '<Rho/r**2>': 256.01273421, '<Rho/r>': 22.954908618, '<Rho*r>': 9.4998961933, '<Rho*r**2>': 15.172894906, '<Rho*r**4>': 80.51045651, 'GR(-2)': -255.50489747, 'GR(-1)': -44.988821679, 'GR0': -25.507286293, 'GR1': -34.656605556, 'GR2': -69.046214277, 'VenO': -183.63926895, 'VenT': -192.68868344, 'Dipole X': -0.0016461566576, 'Dipole Y': -0.25708969568, 'Dipole Z': -0.020646892538, '|Dipole|': 0.25792269313}},
    integration_error = {'O1': -4.0077877571e-05},
    critical_points = ints_critical_points,
    bond_critical_points = ints_critical_points,
    ring_critical_points = {"O1": []},
    cage_critical_points = {"O1": []},
    properties = {'O1': {'iqa': -75.484269717, 'q00': -1.0762060817, 'q10': 1.0692266615609444e-05, 'q11c': -0.18349803115198798, 'q11s': -0.18125282915604815, 'q20': -0.7306931079097068, 'q21c': 4.623931513580379e-05, 'q21s': 6.704284971342138e-05, 'q22c': -0.0072513073463865265, 'q22s': -0.24533386504758276, 'q30': -0.00015693584687446506, 'q31c': -0.6029724012139631, 'q31s': -0.6667364017324746, 'q32c': -3.203842693814914e-05, 'q32s': 0.00022118204528320972, 'q33c': 0.8817616491730934, 'q33s': -0.7111368780157797, 'q40': 2.1290443376840233, 'q41c': -0.00021688230028195056, 'q41s': -3.0547019421551455e-05, 'q42c': -0.08077252353757391, 'q42s': 0.23264809990535876, 'q43c': 0.0005243358460912961, 'q43s': 0.0005797603423474216, 'q44c': 4.139038974866185, 'q44s': 0.7074731781578308}},
    net_charge = {'O1': -1.0762060817},
    global_spherical_multipoles = {'O1': {'q00': -1.0762060817, 'q10': -0.020646892538, 'q11c': -0.0016461566576, 'q11s': -0.25708969568, 'q20': -0.021700469782, 'q21c': -0.75018382635, 'q21s': 0.017792037022, 'q22c': -0.16232546581, 'q22s': 0.065122302165, 'q30': 0.044683217585, 'q31c': -0.089287472207, 'q31s': 0.30596239543, 'q32c': -0.063395331291, 'q32s': -1.391653952, 'q33c': -0.067954891804, 'q33s': 0.20594440588, 'q40': -1.9609913177, 'q41c': 1.1488477959, 'q41s': 0.26702238434, 'q42c': -0.75531442849, 'q42s': -0.39080307859, 'q43c': 3.6310817472, 'q43s': -0.24247145429, 'q44c': -1.7369385615, 'q44s': 0.072615449798, 'q50': -0.41836505357, 'q51c': 0.53462091556, 'q51s': -2.2325774531, 'q52c': -0.13994550028, 'q52s': 1.5489383968, 'q53c': 0.84062227501, 'q53s': -1.567560763, 'q54c': -0.41193097157, 'q54s': 3.1313064283, 'q55c': -0.31126569086, 'q55s': -2.3600710711}},
    local_spherical_multipoles = {'O1': {'q00': -1.0762060817, 'q10': 1.0692266615609444e-05, 'q11c': -0.18349803115198798, 'q11s': -0.18125282915604815, 'q20': -0.7306931079097068, 'q21c': 
4.623931513580379e-05, 'q21s': 6.704284971342138e-05, 'q22c': -0.0072513073463865265, 'q22s': -0.24533386504758276, 'q30': -0.00015693584687446506, 'q31c': -0.6029724012139631, 'q31s': -0.6667364017324746, 'q32c': -3.203842693814914e-05, 'q32s': 0.00022118204528320972, 'q33c': 0.8817616491730934, 'q33s': -0.7111368780157797, 'q40': 2.1290443376840233, 'q41c': -0.00021688230028195056, 'q41s': -3.0547019421551455e-05, 'q42c': -0.08077252353757391, 'q42s': 0.23264809990535876, 'q43c': 0.0005243358460912961, 'q43s': 0.0005797603423474216, 'q44c': 4.139038974866185, 'q44s': 0.7074731781578308}},
    C_matrix_dict = C_matrices_dict,
    iqa_energy_components = {'O1': {'T(A)': 75.03894204, 'Vneen(A,A)/2 = Vne(A,A)': -183.63926895, 'Vne(A,Mol)/2': -93.400150506, 'Ven(A,Mol)/2': -96.344341721, 'Vneen(A,Mol)/2': -189.74449223, "Vne(A,A')/2": -1.5805160326, "Ven(A,A')/2": -4.5247072473, "Vneen(A,A')/2": -6.1052232799, "Vee0(A,A) + Vee0(A,A')/2": 35.538139035, "Vee(A,A) + Vee(A,A')/2": 35.145962157, "VeeC(A,A) + VeeC(A,A')/2": 44.071057668, "VeeX0(A,A) + VeeX0(A,A')/2": -8.5329186324, "VeeX(A,A) + VeeX(A,A')/2": -8.9250955109, 'Vnn(A,Mol)/2': 4.0753183136, 'Vee0(A,A)': 33.972313611, 'Vee(A,A)': 33.580136733, 'VeeC(A,A)': 42.300500739, 'VeeX0(A,A)': -8.3281871282, 'VeeX(A,A)': -8.7203640066, "Vee0(A,A')/2": 1.5658254241, "Vee(A,A')/2": 1.5658254241, "VeeC(A,A')/2": 1.7705569283, "VeeX0(A,A')/2": -0.20473150425, "VeeX(A,A')/2": -0.20473150425, 'V_IQA(A)': -150.52321176, 'VC_IQA(A)': -141.59811625, 'VX_IQA(A)': -8.9250955109, 'V_IQA(A,A)': -150.05913221, 'VC_IQA(A,A)': -141.33876821, 'VX_IQA(A,A)': -8.7203640066, "V_IQA(A,A')/2": -0.46407954221, "VC_IQA(A,A')/2": -0.25934803796, "VX_IQA(A,A')/2": -0.20473150425, 'E_IQA0(A)': -75.092092839, 'E_IQA(A)': -75.484269717, 'E_IQA_Intra0(A)': -74.628013297, 'E_IQA_Intra(A)': -75.020190175, 'E_IQA_Inter0(A)': -0.46407954221, 'E_IQA_Inter(A)': -0.46407954221}},
    iqa = {'O1': -75.484269717},
    e_intra = {'O1': -75.020190175},
    q = {'O1': -1.0762060817},
    q00 = {'O1': -1.0762060817},
    dipole_mag = {'O1': 0.2579226931234475},
    total_time = {'O1': 184},
    
    
    )