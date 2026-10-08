import uuid
from datetime import datetime, timezone
from typing import Optional
import pandas as pd

from app.models.schemas import DatasetSummary

class DatasetStore:
    """In-memory store for uploaded datasets during the hackathon MVP."""
    
    def __init__(self):
        self._datasets: dict[str, dict] = {}

    def add_dataset(self, df: pd.DataFrame, filename: str) -> DatasetSummary:
        dataset_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3)

        self._datasets[dataset_id] = {
            "df": df,
            "filename": filename,
            "created_at": created_at,
            "memory_mb": memory_mb,
        }

        return DatasetSummary(
            dataset_id=dataset_id,
            filename=filename,
            row_count=len(df),
            column_count=len(df.columns),
            columns=[str(c) for c in df.columns],
            memory_mb=memory_mb,
            created_at=created_at,
        )

    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        entry = self._datasets.get(dataset_id)
        if entry:
            return entry["df"]
        return None

    def get_metadata(self, dataset_id: str) -> Optional[dict]:
        entry = self._datasets.get(dataset_id)
        if entry:
            return {
                "dataset_id": dataset_id,
                "filename": entry["filename"],
                "created_at": entry["created_at"],
                "memory_mb": entry["memory_mb"],
                "row_count": len(entry["df"]),
                "column_count": len(entry["df"].columns),
                "columns": [str(c) for c in entry["df"].columns],
            }
        return None

    def list_datasets(self) -> list[DatasetSummary]:
        summaries = []
        for dataset_id, entry in self._datasets.items():
            df = entry["df"]
            summaries.append(
                DatasetSummary(
                    dataset_id=dataset_id,
                    filename=entry["filename"],
                    row_count=len(df),
                    column_count=len(df.columns),
                    columns=[str(c) for c in df.columns],
                    memory_mb=entry["memory_mb"],
                    created_at=entry["created_at"],
                )
            )
        return summaries

    def delete_dataset(self, dataset_id: str) -> bool:
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
            return True
        return False

    def clear(self):
        self._datasets.clear()

dataset_store = DatasetStore()
