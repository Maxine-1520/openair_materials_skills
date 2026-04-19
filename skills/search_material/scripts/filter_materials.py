#!/usr/bin/env python3
"""
Filter 2D semiconductor single crystal materials from Materials Project database.

This script searches the Materials Project database for materials that meet the following criteria:
1. Two-dimensional (2D) layered structure
2. Semiconductor properties (band gap in specified range)
3. Single crystal structure (low energy above hull)

Usage:
    python filter_2d_semiconductors_MP.py [options]

Examples:
    python filter_2d_semiconductors_MP.py --band-gap-min 0.5 --band-gap-max 3.0
    python filter_2d_semiconductors_MP.py --elements C N --max-results 50
    python filter_2d_semiconductors_MP.py --output 2d_semiconductors.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import os
import json

try:
    from mp_api.client import MPRester
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from pymatgen.analysis.dimensionality import get_dimensionality_larsen
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("\nInstall required packages with:")
    print("  pip install mp-api pymatgen")
    sys.exit(1)


# Scoring weights for material recommendation
PROPERTY_WEIGHTS = {
    'band_gap': 0.15,           # 带隙适中性
    'stability': 0.20,          # 热力学稳定性
    'dielectric': 0.10,         # 介电常数
    'piezoelectric': 0.15,      # 压电性能
    'magnetic': 0.10,           # 磁性/自旋极化
    'anisotropy': 0.10,         # 各向异性
    'elasticity': 0.10,         # 弹性模量
    'dimensionality': 0.10,     # 二维特征明确性
}


def is_layered_structure(structure: Structure, c_axis_threshold: float = 1.3) -> bool:
    """
    Determine if a structure is layered (2D) based on lattice parameters.

    A structure is considered layered if:
    1. The c-axis is significantly longer than a and b axes
    2. Or use pymatgen's dimensionality analysis

    Args:
        structure: Pymatgen Structure object
        c_axis_threshold: Ratio threshold for c/(a+b)/2

    Returns:
        True if structure appears to be 2D/layered
    """
    try:
        # Method 1: Use pymatgen's dimensionality analysis
        dimensionality = get_dimensionality_larsen(structure)
        if dimensionality == 2:
            return True
    except Exception as e:
        print(f"  Warning: Dimensionality analysis failed: {e}")

    # Method 2: Check lattice parameter ratios
    lattice = structure.lattice
    a, b, c = lattice.a, lattice.b, lattice.c

    # Check if c-axis is significantly larger (indicating layered structure)
    avg_ab = (a + b) / 2
    if c / avg_ab > c_axis_threshold:
        return True

    # Check if one axis is significantly smaller (thin layer)
    if min(a, b, c) / max(a, b, c) < 0.5:
        return True

    return False


def analyze_structure_2d_features(structure: Structure) -> Dict:
    """
    Analyze 2D-related features of a structure.

    Args:
        structure: Pymatgen Structure object

    Returns:
        Dictionary with 2D analysis results
    """
    features = {}

    # Lattice parameters
    lattice = structure.lattice
    features['lattice_a'] = lattice.a
    features['lattice_b'] = lattice.b
    features['lattice_c'] = lattice.c
    features['c_to_ab_ratio'] = lattice.c / ((lattice.a + lattice.b) / 2)

    # Try dimensionality analysis
    try:
        dim = get_dimensionality_larsen(structure)
        features['dimensionality'] = dim
    except:
        features['dimensionality'] = None

    # Space group analysis
    try:
        sga = SpacegroupAnalyzer(structure)
        features['spacegroup_number'] = sga.get_space_group_number()
        features['spacegroup_symbol'] = sga.get_space_group_symbol()
        features['crystal_system'] = sga.get_crystal_system()
    except:
        features['spacegroup_number'] = None
        features['spacegroup_symbol'] = None
        features['crystal_system'] = None

    return features


def get_comprehensive_properties(mpr: MPRester, material_id: str) -> Dict:
    """
    Get comprehensive material properties from Materials Project.

    Args:
        mpr: MPRester client instance
        material_id: Material ID

    Returns:
        Dictionary with all available properties
    """
    properties = {}

    # Try to get dielectric properties
    try:
        dielectric_data = mpr.materials.dielectric.search(material_ids=[material_id])
        if dielectric_data:
            mat = dielectric_data[0]
            properties['dielectric_electronic'] = mat.e_electronic if hasattr(mat, 'e_electronic') else None
            properties['dielectric_total'] = mat.e_total if hasattr(mat, 'e_total') else None
            properties['refractive_index'] = mat.n if hasattr(mat, 'n') else None
    except:
        properties['dielectric_electronic'] = None
        properties['dielectric_total'] = None
        properties['refractive_index'] = None

    # Try to get piezoelectric properties
    try:
        piezo_data = mpr.materials.piezoelectric.search(material_ids=[material_id])
        if piezo_data:
            mat = piezo_data[0]
            properties['piezoelectric_modulus'] = mat.piezoelectric_modulus if hasattr(mat, 'piezoelectric_modulus') else None
            properties['has_piezoelectric'] = True
        else:
            properties['piezoelectric_modulus'] = None
            properties['has_piezoelectric'] = False
    except:
        properties['piezoelectric_modulus'] = None
        properties['has_piezoelectric'] = False

    # Try to get elasticity properties
    try:
        elastic_data = mpr.materials.elasticity.search(material_ids=[material_id])
        if elastic_data:
            mat = elastic_data[0]
            properties['bulk_modulus'] = mat.bulk_modulus_vrh if hasattr(mat, 'bulk_modulus_vrh') else None
            properties['shear_modulus'] = mat.shear_modulus_vrh if hasattr(mat, 'shear_modulus_vrh') else None
            properties['elastic_anisotropy'] = mat.universal_anisotropy if hasattr(mat, 'universal_anisotropy') else None
        else:
            properties['bulk_modulus'] = None
            properties['shear_modulus'] = None
            properties['elastic_anisotropy'] = None
    except:
        properties['bulk_modulus'] = None
        properties['shear_modulus'] = None
        properties['elastic_anisotropy'] = None

    return properties


def calculate_material_score(material: Dict, target_band_gap: float = 1.5) -> Dict:
    """
    Calculate comprehensive score for material recommendation.

    Args:
        material: Material properties dictionary
        target_band_gap: Target band gap value (eV)

    Returns:
        Dictionary with scores and total score
    """
    scores = {}

    # 1. Band gap score (closer to target is better)
    if material.get('band_gap') is not None:
        gap_diff = abs(material['band_gap'] - target_band_gap)
        scores['band_gap'] = max(0, 1 - gap_diff / 3.0)  # Normalize to 0-1
    else:
        scores['band_gap'] = 0

    # 2. Stability score (lower energy above hull is better)
    if material.get('energy_above_hull') is not None:
        scores['stability'] = max(0, 1 - material['energy_above_hull'] / 0.1)
    else:
        scores['stability'] = 0

    # 3. Dielectric score (moderate values preferred)
    if material.get('dielectric_electronic') is not None:
        # Prefer dielectric constant in range 5-20
        diel = material['dielectric_electronic']
        if 5 <= diel <= 20:
            scores['dielectric'] = 1.0
        elif diel < 5:
            scores['dielectric'] = diel / 5.0
        else:
            scores['dielectric'] = max(0, 1 - (diel - 20) / 30)
    else:
        scores['dielectric'] = 0.5  # Neutral if unknown

    # 4. Piezoelectric score
    if material.get('has_piezoelectric'):
        if material.get('piezoelectric_modulus') is not None:
            # Higher piezoelectric modulus is better
            scores['piezoelectric'] = min(1.0, material['piezoelectric_modulus'] / 10.0)
        else:
            scores['piezoelectric'] = 0.7  # Has property but no value
    else:
        scores['piezoelectric'] = 0

    # 5. Magnetic score (presence of magnetism is valuable)
    if material.get('is_magnetic'):
        scores['magnetic'] = 1.0
    else:
        scores['magnetic'] = 0.3  # Non-magnetic still has some value

    # 6. Anisotropy score (higher anisotropy for 2D materials)
    if material.get('elastic_anisotropy') is not None:
        # Higher anisotropy indicates stronger 2D character
        scores['anisotropy'] = min(1.0, material['elastic_anisotropy'] / 5.0)
    else:
        scores['anisotropy'] = 0.5

    # 7. Elasticity score (moderate values preferred)
    if material.get('bulk_modulus') is not None:
        # Prefer bulk modulus 50-200 GPa
        bulk = material['bulk_modulus']
        if 50 <= bulk <= 200:
            scores['elasticity'] = 1.0
        else:
            scores['elasticity'] = max(0, 1 - abs(bulk - 125) / 200)
    else:
        scores['elasticity'] = 0.5

    # 8. Dimensionality score
    if material.get('dimensionality') == 2:
        scores['dimensionality'] = 1.0
    elif material.get('c_to_ab_ratio') is not None and material['c_to_ab_ratio'] > 1.3:
        scores['dimensionality'] = 0.8
    else:
        scores['dimensionality'] = 0.5

    # Calculate weighted total score
    total_score = sum(scores[key] * PROPERTY_WEIGHTS[key] for key in scores)

    return {
        'scores': scores,
        'total_score': total_score
    }


def filter_2d_semiconductors(
    api_key: Optional[str] = None,
    elements: Optional[List[str]] = None,
    band_gap_min: float = 0.5,
    band_gap_max: float = 3.0,
    target_band_gap: float = 1.5,
    energy_above_hull_max: float = 0.05,
    max_results: int = 10,
    verbose: bool = True
) -> List[Dict]:
    """
    Filter 2D semiconductor materials from Materials Project.

    Args:
        api_key: Materials Project API key (or use MP_API_KEY env variable)
        elements: List of elements to include in search
        band_gap_min: Minimum band gap (eV) for semiconductors
        band_gap_max: Maximum band gap (eV) for semiconductors
        energy_above_hull_max: Maximum energy above hull (eV/atom) for stability
        max_results: Maximum number of results to return
        verbose: Print progress information

    Returns:
        List of dictionaries containing filtered material information
    """
    results = []

    if verbose:
        print("="*70)
        print("2D SEMICONDUCTOR MATERIAL FILTER")
        print("="*70)
        print(f"\nSearch criteria:")
        print(f"  Band gap range:        {band_gap_min} - {band_gap_max} eV")
        print(f"  Energy above hull:     < {energy_above_hull_max} eV/atom")
        print(f"  Elements:              {elements if elements else 'All'}")
        print(f"  Max results:           {max_results}")
        print()

    try:
        with MPRester(api_key) as mpr:
            # Step 1: Query Materials Project with basic filters
            if verbose:
                print("Step 1: Querying Materials Project database...")

            search_params = {
                'band_gap': (band_gap_min, band_gap_max),
                'energy_above_hull': (0, energy_above_hull_max),
                'is_stable': True,
            }

            if elements:
                search_params['elements'] = elements

            materials = mpr.materials.summary.search(**search_params)

            if verbose:
                print(f"  Found {len(materials)} materials matching basic criteria")

            # Step 2: Filter for 2D structures
            if verbose:
                print("\nStep 2: Analyzing structures for 2D characteristics...")

            count = 0
            for i, mat in enumerate(materials):
                if count >= max_results:
                    break

                try:
                    # Get structure
                    structure = mpr.get_structure_by_material_id(mat.material_id)

                    # Check if layered/2D
                    if is_layered_structure(structure):
                        # Analyze 2D features
                        features = analyze_structure_2d_features(structure)

                        # Get comprehensive properties
                        comp_props = get_comprehensive_properties(mpr, mat.material_id)

                        # Compile result
                        result = {
                            'material_id': mat.material_id,
                            'formula': mat.formula_pretty,
                            'band_gap': mat.band_gap,
                            'energy_above_hull': mat.energy_above_hull,
                            'formation_energy_per_atom': mat.formation_energy_per_atom,
                            'density': mat.density,
                            'is_magnetic': mat.is_magnetic if hasattr(mat, 'is_magnetic') else None,
                            'lattice_a': features['lattice_a'],
                            'lattice_b': features['lattice_b'],
                            'lattice_c': features['lattice_c'],
                            'c_to_ab_ratio': features['c_to_ab_ratio'],
                            'dimensionality': features['dimensionality'],
                            'spacegroup_number': features['spacegroup_number'],
                            'spacegroup_symbol': features['spacegroup_symbol'],
                            'crystal_system': features['crystal_system'],
                            # Add comprehensive properties
                            'dielectric_electronic': comp_props.get('dielectric_electronic'),
                            'dielectric_total': comp_props.get('dielectric_total'),
                            'refractive_index': comp_props.get('refractive_index'),
                            'piezoelectric_modulus': comp_props.get('piezoelectric_modulus'),
                            'has_piezoelectric': comp_props.get('has_piezoelectric'),
                            'bulk_modulus': comp_props.get('bulk_modulus'),
                            'shear_modulus': comp_props.get('shear_modulus'),
                            'elastic_anisotropy': comp_props.get('elastic_anisotropy'),
                        }

                        # Calculate recommendation score
                        score_data = calculate_material_score(result, target_band_gap=target_band_gap)
                        result['recommendation_score'] = score_data['total_score']
                        result['property_scores'] = score_data['scores']

                        results.append(result)
                        count += 1

                        if verbose:
                            print(f"  [{count}] {mat.formula_pretty} ({mat.material_id})")
                            print(f"      Band gap: {mat.band_gap:.2f} eV")
                            print(f"      Score: {score_data['total_score']:.3f}")
                            if comp_props.get('has_piezoelectric'):
                                print(f"      Piezoelectric: Yes")
                            if mat.is_magnetic if hasattr(mat, 'is_magnetic') else False:
                                print(f"      Magnetic: Yes")

                except Exception as e:
                    if verbose:
                        print(f"  Error processing {mat.material_id}: {e}")
                    continue

    except Exception as e:
        print(f"\nError accessing Materials Project: {e}")
        print("\nPlease ensure:")
        print("  1. You have set MP_API_KEY environment variable")
        print("  2. Your API key is valid")
        print("  3. You have internet connection")
        sys.exit(1)

    if verbose:
        print(f"\n{'='*70}")
        print(f"Total 2D semiconductors found: {len(results)}")
        print(f"{'='*70}\n")

    # Sort by recommendation score
    results.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)


    '''
    # Step 3: Check literature reports from internet
    if results and verbose:
        print(f"\nStep 3: Checking literature reports from internet...")

    try:
        # Load configuration
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                lit_config = config.get('literature_search', {})
        else:
            lit_config = {}

        # Import and use literature checker
        from literature_checker import LiteratureChecker
        lit_checker = LiteratureChecker(lit_config)
        results = lit_checker.batch_check(results, verbose=verbose)

        if verbose:
            reported_count = sum(1 for r in results if r.get('literature_report', {}).get('is_reported'))
            print(f"  Literature check completed: {reported_count}/{len(results)} materials found in literature")
    except Exception as e:
        if verbose:
            print(f"  Warning: Literature check failed: {e}")
            print(f"  Continuing without literature information...")
        # Add empty literature_report for all materials
        for result in results:
            if 'literature_report' not in result:
                result['literature_report'] = {
                    'is_reported': None,
                    'paper_count': 0,
                    'papers': [],
                    'methods': []
                }
    '''

    return results


def export_results(results: List[Dict], output_file: str, format: str = 'json'):
    """
    Export filtered results to file.

    Args:
        results: List of material dictionaries
        output_file: Output file path
        format: Export format ('json' or 'csv')
    """
    if format == 'json':
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results exported to {output_file}")

    elif format == 'csv':
        try:
            import csv
            if len(results) > 0:
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
                print(f"Results exported to {output_file}")
            else:
                print("No results to export")
        except ImportError:
            print("Error: csv module not available")


def print_summary(results: List[Dict]):
    """
    Print comprehensive summary statistics and recommendations.

    Args:
        results: List of material dictionaries (sorted by score)
    """
    if not results:
        print("No materials found matching criteria")
        return
    
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Results saved to results.json")

    print("\n" + "="*70)
    print("COMPREHENSIVE MATERIAL ANALYSIS & RECOMMENDATIONS")
    print("="*70)

    # Overall statistics
    print(f"\nTotal materials analyzed: {len(results)}")

    # Band gap statistics
    band_gaps = [r['band_gap'] for r in results if r['band_gap'] is not None]
    if band_gaps:
        print(f"\nBand gap statistics:")
        print(f"  Range: {min(band_gaps):.2f} - {max(band_gaps):.2f} eV")
        print(f"  Average: {sum(band_gaps)/len(band_gaps):.2f} eV")

    # Stability statistics
    energies = [r['energy_above_hull'] for r in results if r['energy_above_hull'] is not None]
    if energies:
        print(f"\nStability (Energy above hull):")
        print(f"  Range: {min(energies):.4f} - {max(energies):.4f} eV/atom")
        print(f"  Average: {sum(energies)/len(energies):.4f} eV/atom")

    # Special properties count
    piezo_count = sum(1 for r in results if r.get('has_piezoelectric'))
    magnetic_count = sum(1 for r in results if r.get('is_magnetic'))
    print(f"\nSpecial properties:")
    print(f"  Piezoelectric materials: {piezo_count}")
    print(f"  Magnetic materials: {magnetic_count}")

    # Crystal systems distribution
    crystal_systems = [r['crystal_system'] for r in results if r['crystal_system'] is not None]
    if crystal_systems:
        from collections import Counter
        system_counts = Counter(crystal_systems)
        print(f"\nCrystal systems distribution:")
        for system, count in system_counts.most_common():
            print(f"  {system}: {count}")

    # Literature report statistics
    lit_reports = [r.get('literature_report', {}) for r in results]
    reported_count = sum(1 for lr in lit_reports if lr.get('is_reported'))
    unreported_count = sum(1 for lr in lit_reports if lr.get('is_reported') == False)

    if reported_count > 0 or unreported_count > 0:
        print(f"\nLiterature report status:")
        print(f"  Reported in literature: {reported_count}")
        print(f"  Not reported: {unreported_count}")
        if len(results) > reported_count + unreported_count:
            print(f"  Unknown: {len(results) - reported_count - unreported_count}")

    # Top recommended materials
    print("\n" + "="*70)
    print("TOP 10 RECOMMENDED MATERIALS (by comprehensive score)")
    print("="*70)

    for i, mat in enumerate(results[:10], 1):
        print(f"\n{i}. {mat['formula']} ({mat['material_id']})")
        print(f"   Overall Score: {mat.get('recommendation_score', 0):.3f}")
        print(f"   Band Gap: {mat['band_gap']:.2f} eV")
        print(f"   Stability: {mat['energy_above_hull']:.4f} eV/atom")

        # Show available properties
        props = []
        if mat.get('dielectric_electronic'):
            props.append(f"ε={mat['dielectric_electronic']:.1f}")
        if mat.get('has_piezoelectric'):
            if mat.get('piezoelectric_modulus'):
                props.append(f"Piezo={mat['piezoelectric_modulus']:.2f}")
            else:
                props.append("Piezoelectric")
        if mat.get('is_magnetic'):
            props.append("Magnetic")
        if mat.get('elastic_anisotropy'):
            props.append(f"Aniso={mat['elastic_anisotropy']:.2f}")

        if props:
            print(f"   Properties: {', '.join(props)}")

        print(f"   Space Group: {mat.get('spacegroup_symbol', 'N/A')}")
        print(f"   Dimensionality: {mat.get('dimensionality', 'N/A')}")

        # Show literature report
        # lit_report = mat.get('literature_report', {})
        # if lit_report.get('is_reported') is not None:
        #     print(f"\n   Literature Report:")
        #     if lit_report.get('is_reported'):
        #         print(f"      Status: ✓ Reported in literature")
        #         print(f"      Papers found: {lit_report.get('paper_count', 0)}")

        #         methods = lit_report.get('methods', [])
        #         if methods:
        #             print(f"      Synthesis methods: {', '.join(methods)}")

        #         papers = lit_report.get('papers', [])
        #         if papers:
        #             print(f"      References:")
        #             for paper in papers[:3]:  # Show max 3 papers
        #                 title = paper.get('title', 'N/A')
        #                 year = paper.get('year', 'N/A')
        #                 doi = paper.get('doi', '')
        #                 if len(title) > 60:
        #                     title = title[:57] + "..."
        #                 print(f"         - {title} ({year})")
        #                 if doi:
        #                     print(f"           DOI: {doi}")
        #     else:
        #         print(f"      Status: ✗ Not reported in literature")
        #         print(f"      Note: Novel material candidate for synthesis")

    print("\n" + "="*70 + "\n")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Filter 2D semiconductor single crystal materials from Materials Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search for 2D semiconductors
  python filter_2d_semiconductors.py

  # Search with specific band gap range
  python filter_2d_semiconductors.py --band-gap-min 1.0 --band-gap-max 2.5

  # Search for materials containing specific elements
  python filter_2d_semiconductors.py --elements C N

  # Export results to JSON file
  python filter_2d_semiconductors.py --output 2d_semiconductors.json

  # Export to CSV format
  python filter_2d_semiconductors.py --output results.csv --format csv

  # Limit number of results
  python filter_2d_semiconductors.py --max-results 20

Environment Variables:
  MP_API_KEY    Materials Project API key (required)
                Get your key from: https://next-gen.materialsproject.org/
        """
    )

    parser.add_argument(
        '--api-key',
        help='Materials Project API key (or set MP_API_KEY environment variable)'
    )

    parser.add_argument(
        '--elements', '-e',
        nargs='+',
        help='Elements to include in search (e.g., C N Si). Search all elements if not provided'
    )

    parser.add_argument(
        '--band-gap-min',
        type=float,
        default=0.5,
        help='Minimum band gap in eV (default: 0.5)'
    )

    parser.add_argument(
        '--band-gap-max',
        type=float,
        default=3.0,
        help='Maximum band gap in eV (default: 3.0)'
    )

    parser.add_argument(
        '--target-band-gap',
        type=float,
        default=1.5,
        help='Target band gap for scoring in eV (default: 1.5)'
    )

    parser.add_argument(
        '--energy-above-hull-max',
        type=float,
        default=0.05,
        help='Maximum energy above hull in eV/atom (default: 0.05)'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum number of results to return (default: 10)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path for results'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )

    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='Skip printing summary statistics'
    )

    args = parser.parse_args()

    # Get API key
    import dotenv
    dotenv.load_dotenv()
    api_key = args.api_key or os.environ.get('MP_API_KEY')
    if not api_key:
        print("Error: Materials Project API key not provided")
        print("\nPlease either:")
        print("  1. Set MP_API_KEY environment variable:")
        print("     export MP_API_KEY='your_api_key_here'")
        print("  2. Use --api-key argument:")
        print("     python filter_2d_semiconductors.py --api-key your_api_key_here")
        print("\nGet your API key from: https://next-gen.materialsproject.org/")
        sys.exit(1)

    # Run filter
    results = filter_2d_semiconductors(
        api_key=api_key,
        elements=args.elements,
        band_gap_min=args.band_gap_min,
        band_gap_max=args.band_gap_max,
        target_band_gap=args.target_band_gap,
        energy_above_hull_max=args.energy_above_hull_max,
        max_results=args.max_results,
        verbose=not args.quiet
    )

    # Print summary
    if not args.no_summary and not args.quiet:
        print_summary(results)

    # Export results
    if args.output:
        export_results(results, args.output, args.format)
    elif not args.quiet:
        print("Tip: Use --output to save results to a file")


if __name__ == "__main__":
    main()
