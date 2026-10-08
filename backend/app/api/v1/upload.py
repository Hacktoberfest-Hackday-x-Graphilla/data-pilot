import io
from fastapi import APIRouter, File, HTTPException, UploadFile, status
import pandas as pd

from app.models.schemas import DatasetSummary
from app.services.dataset_store import dataset_store

router = APIRouter(prefix="/datasets")

@router.post("/upload", response_model=DatasetSummary, status_code=status.HTTP_201_CREATED)
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads, validates, and parses a CSV dataset into memory."""
    filename = file.filename or "dataset.csv"
    
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format for '{filename}'. Only .csv files are supported.",
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file is empty.",
        )

    # Attempt parsing with encoding fallbacks (utf-8, latin1)
    df = None
    parse_errors = []
    for encoding in ["utf-8", "latin1", "cp1252"]:
        try:
            buffer = io.BytesIO(content)
            df = pd.read_csv(buffer, encoding=encoding)
            break
        except Exception as e:
            parse_errors.append(f"{encoding}: {str(e)}")

    if df is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file as CSV. Parsing errors: {'; '.join(parse_errors)}",
        )

    if df.empty and len(df.columns) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The parsed dataset contains no columns or data rows.",
        )

    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    summary = dataset_store.add_dataset(df, filename=filename)
    return summary

@router.get("", response_model=list[DatasetSummary])
def list_datasets():
    """Lists all datasets currently loaded in memory."""
    return dataset_store.list_datasets()

@router.get("/{dataset_id}", response_model=DatasetSummary)
def get_dataset_summary(dataset_id: str):
    """Retrieves metadata summary for a dataset."""
    metadata = dataset_store.get_metadata(dataset_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return DatasetSummary(**metadata)

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: str):
    """Removes a dataset from memory."""
    deleted = dataset_store.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )
    return None
