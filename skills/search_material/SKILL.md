---
name: mp-material-search
description: |
  Search and filter 2D semiconductor materials from Materials Project (MP) database.
  Use this skill whenever the user wants to:
  - Find 2D semiconductor materials from Materials Project
  - Search for materials with specific band gap ranges
  - Filter materials by elements (e.g., "C", "N", "Si")
  - Get material recommendations based on multiple properties (dielectric, piezoelectric, magnetic, etc.)
  - Analyze crystal structures for 2D dimensionality
  - Query the MP database for semiconductor materials

  This skill wraps the mp-api library to query Materials Project and filters results for 2D/layered semiconductor materials with comprehensive property scoring.
compatibility: mp-api, pymatgen, flask
---

# MP Materials Search Skill

This skill enables intelligent search and filtering of 2D semiconductor materials from the Materials Project database. The agent automatically determines optimal search parameters based on user requirements.

## Core Search Function

Use the bundled `filter_materials.py` script to search Materials Project:

```bash
python skills/mp-material-search/scripts/filter_materials.py [options]
```

## Search Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--elements` | Element symbols (e.g., C N Si) | All elements |
| `--band-gap-min` | Minimum band gap (eV) | 0.5 |
| `--band-gap-max` | Maximum band gap (eV) | 3.0 |
| `--target-band-gap` | Target band gap for scoring (eV) | 1.5 |
| `--energy-above-hull-max` | Max energy above hull (eV/atom) | 0.05 |
| `--max-results` | Maximum number of results | 10 |
| `--api-key` | MP API key (or set MP_API_KEY env) | Required |

## How to Search

### Step 1: Understand User Requirements

Ask clarifying questions if needed:
- What elements should the material contain?
- What band gap range is acceptable?
- Is stability (low energy above hull) important?
- Any specific properties needed? (piezoelectric, magnetic, etc.)

### Step 2: Execute Search

Run the filter script with appropriate parameters:

```bash
cd <project-root>
export MP_API_KEY=<api_key>
python skills/mp-material-search/scripts/filter_materials.py \
  --elements <elements> \
  --band-gap-min <min> \
  --band-gap-max <max> \
  --max-results <num>
```

### Step 3: Present Results

The search returns a JSON array with comprehensive material data:
- Basic info: material_id, formula, band_gap, energy_above_hull
- Structure: lattice parameters, spacegroup, crystal_system
- Properties: dielectric, piezoelectric, magnetic, elastic anisotropy
- Recommendation score (0-1, higher is better)

Present top results with:
1. Formula and material ID
2. Band gap and stability
3. Special properties (piezoelectric, magnetic, etc.)
4. Recommendation score

## Example Searches

### Search for C-based 2D semiconductors
```bash
python skills/mp-material-search/scripts/filter_materials.py \
  --elements C \
  --band-gap-min 0.5 \
  --band-gap-max 2.0
```

### Search for piezoelectric 2D materials
```bash
python skills/mp-material-search/scripts/filter_materials.py \
  --band-gap-min 0.5 \
  --band-gap-max 3.0 \
  --max-results 20
```

### Search with specific target band gap
```bash
python skills/mp-material-search/scripts/filter_materials.py \
  --elements Mo S \
  --target-band-gap 1.5 \
  --max-results 15
```

## Output Format

Results are saved to `results.json` in the project root. The output includes:
- `material_id`: MP material ID
- `formula`: Chemical formula
- `band_gap`: Band gap in eV
- `energy_above_hull`: Thermodynamic stability
- `recommendation_score`: Overall score (0-1)
- `property_scores`: Breakdown of scores by category
- Structure and property details

## API Key Setup

Users need a Materials Project API key:
1. Sign up at https://next-gen.materialsproject.org/
2. Set `MP_API_KEY` environment variable or use `--api-key` argument

## Bundled Scripts

- `scripts/filter_materials.py`: Main search script (adapted from Step1_new_materials)
- `scripts/setup_env.sh`: Environment setup helper
