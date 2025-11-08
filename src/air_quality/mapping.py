"""air_quality.mapping

Centralized three-level column mapping utility.

Resolution order:
1) Explicit mapping (if provided) canonical->original column name
2) Exact match on canonical name (case-insensitive)
3) Synonym-based resolution (case-insensitive); must yield a unique match

On failure:
- Missing required columns -> SchemaError with list of missing
- Ambiguous matches -> SchemaError with candidates listed per field

This utility performs only column-level operations (no row-wise loops).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

import pandas as pd

from .exceptions import SchemaError


@dataclass(slots=True)
class ColumnMappingResult:
    """Result of a mapping operation.

    Attributes
    ----------
    df_mapped: pd.DataFrame
        A DataFrame with canonical column names mapped from the input.
    mapping: Dict[str, str]
        Mapping from canonical column name -> original input column name.
    diagnostics: List[str]
        Human-readable diagnostics (e.g., which synonyms matched).
    candidates: Dict[str, List[str]]
        For each canonical field, the candidate input columns considered (for debugging/reporting).
    """

    df_mapped: pd.DataFrame
    mapping: Dict[str, str]
    diagnostics: List[str]
    candidates: Dict[str, List[str]]


class ColumnMapper:
    @staticmethod
    def map(
        df: pd.DataFrame,
        *,
        required: Sequence[str],
        synonyms: Mapping[str, Sequence[str]] | None = None,
        explicit: Mapping[str, str] | None = None,
        include_candidate_suggestions: bool = False,
    ) -> ColumnMappingResult:
        """Map user-provided DataFrame columns into a canonical schema.

        Parameters
        ----------
        df: pd.DataFrame
            Input data with arbitrary column names.
        required: Sequence[str]
            Canonical column names that must be present after mapping.
        synonyms: Mapping[str, Sequence[str]] | None
            Per-canonical list of acceptable alternative names (case-insensitive).
        explicit: Mapping[str, str] | None
            Optional explicit mapping canonical->original; validated against df columns.
        include_candidate_suggestions: bool
            If True, diagnostics will include candidate suggestions for unresolved fields
            (missing or ambiguous). Default: False.

        Returns
        -------
        ColumnMappingResult

        Raises
        ------
        SchemaError
            If required fields are missing or ambiguous.
        """

        synonyms = synonyms or {}
        explicit = explicit or {}

        # Normalize input columns for case-insensitive matching
        original_cols: List[str] = list(df.columns)
        norm_to_original: Dict[str, str] = {c.lower(): c for c in original_cols}

        diagnostics: List[str] = []
        candidates_map: Dict[str, List[str]] = {}
        mapping: Dict[str, str] = {}

        # 1) Apply explicit mapping where provided
        for canon, orig in explicit.items():
            if orig not in df.columns:
                raise SchemaError(
                    f"Explicit mapping refers to missing column: {orig} for {canon}"
                )
            mapping[canon] = orig
            diagnostics.append(f"explicit: {canon} -> {orig}")

        # Helper to determine candidates for a canonical field
        def find_candidates(canon: str) -> List[str]:
            cands: List[str] = []
            # exact canonical match
            canon_norm = canon.lower()
            if canon_norm in norm_to_original:
                cands.append(norm_to_original[canon_norm])
            # synonyms
            for syn in synonyms.get(canon, []):
                syn_norm = syn.lower()
                # Any input column that equals this synonym (case-insensitive)
                if (
                    syn_norm in norm_to_original
                    and norm_to_original[syn_norm] not in cands
                ):
                    cands.append(norm_to_original[syn_norm])
            return cands

        # 2) Resolve remaining required canonicals
        missing: List[str] = []
        ambiguous: List[Tuple[str, List[str]]] = []

        for canon in required:
            if canon in mapping:
                continue
            cands = find_candidates(canon)
            candidates_map[canon] = list(cands)
            if not cands:
                missing.append(canon)
            elif len(cands) == 1:
                mapping[canon] = cands[0]
                diagnostics.append(f"auto: {canon} -> {cands[0]}")
            else:
                ambiguous.append((canon, cands))

        if ambiguous:
            if include_candidate_suggestions:
                for canon, cands in ambiguous:
                    diagnostics.append(
                        f"unresolved (ambiguous): {canon} - candidates: {cands}"
                    )
            details = ", ".join([f"{c} candidates={v}" for c, v in ambiguous])
            raise SchemaError(f"Ambiguous column mapping: {details}")

        if missing:
            if include_candidate_suggestions:
                for canon in missing:
                    # Check if there are any close matches in available columns
                    available = [c for c in original_cols if c not in mapping.values()]
                    if available:
                        diagnostics.append(
                            f"unresolved (missing): {canon} - available columns: {available}"
                        )
                    else:
                        diagnostics.append(
                            f"unresolved (missing): {canon} - no available columns"
                        )
            raise SchemaError(f"Missing required columns after mapping: {missing}")

        # Construct mapped DataFrame with canonical names
        # Note: This selects columns; pandas may copy views internally, but no row-wise ops are performed.
        mapped_df = pd.DataFrame({canon: df[orig] for canon, orig in mapping.items()})

        return ColumnMappingResult(
            df_mapped=mapped_df,
            mapping=mapping,
            diagnostics=diagnostics,
            candidates=candidates_map,
        )
