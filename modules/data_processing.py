import pandas as pd
import json
import structlog

logger = structlog.get_logger()

SERIALIZERS = {
    "json": lambda df, path: df.to_json(f"{path}.json", orient="records"),
    "parquet": lambda df, path: df.to_parquet(f"{path}.parquet"),
    "csv": lambda df, path: df.to_csv(f"{path}.csv", index=False),
    "excel": lambda df, path: df.to_excel(f"{path}.xlsx", index=False),
}


def process_txt(file_content):
    """
    Processes text file content into a DataFrame.
    """
    data = []
    lines = file_content.split("\n")[1:]  # Skip header
    for row in lines:
        columns = row.split(",")  # Assuming CSV-like structure
        data.append(columns)

    df = pd.DataFrame(data)
    logger.info("TXT file processed", records=len(df))
    return df


def process_json(json_content):
    """
    Processes JSON data into a DataFrame.
    """
    try:
        data = json.loads(json_content)
        df = pd.DataFrame(data)
        logger.info("JSON file processed", records=len(df))
        return df
    except Exception as e:
        logger.error("Failed to process JSON file", error=str(e))
        raise


def process_parquet(parquet_path):
    """
    Processes Parquet data into a DataFrame.
    """
    try:
        df = pd.read_parquet(parquet_path)
        logger.info("Parquet file processed", records=len(df))
        return df
    except Exception as e:
        logger.error("Failed to process Parquet file", error=str(e))
        raise


def process_excel(file_path):
    """
    Processes Excel files into a DataFrame.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
        logger.info("Excel file processed", sheets=list(df.keys()))
        return df  # Returns dictionary {sheet_name: DataFrame}
    except Exception as e:
        logger.error("Failed to process Excel file", error=str(e))
        raise


def process_file(file_path, file_type):
    """
    Determines which processing function to call based on file type.
    """
    processors = {
        "txt": process_txt,
        "json": process_json,
        "parquet": process_parquet,
        "excel": process_excel,
    }

    if file_type not in processors:
        raise ValueError(f"Unsupported file type: {file_type}")

    logger.info("Processing file", file_path=file_path, file_type=file_type)
    return processors[file_type](file_path)


def enforce_snowflake_schema(dataframe, schema):
    """
    Ensures the dataframe aligns with the Snowflake schema by:
    - Adding missing columns with NULL values.
    - Enforcing per-column NOT NULL constraints.
    """
    expected_columns = {col["name"]: col for col in schema}

    # Add missing columns with NULL values
    for column, column_info in expected_columns.items():
        if column not in dataframe.columns:
            dataframe[column] = None

    # Reorder columns to match schema definition
    dataframe = dataframe[list(expected_columns.keys())]

    # Enforce per-column NOT NULL constraints
    for column, column_info in expected_columns.items():
        if column_info.get(
            "enforce_not_null", False
        ):  # Default to False if not specified
            dataframe[column].fillna(
                "", inplace=True
            )  # Replace NULLs with empty string

    logger.info("Schema alignment completed with per-column NOT NULL enforcement")
    return dataframe


def transform_data(
    file_path,
    file_type,
    schema,
    output_format="json",
    output_directory="/tmp/default_output",
    filename="unknown_file",
):
    """
    Transforms data while ensuring Snowflake schema compatibility.
    """
    dataframe = process_file(file_path, file_type)
    dataframe["filename"] = filename
    dataframe["received_at"] = pd.Timestamp.now()

    # Convert each row into JSON string (for Snowflake VARIANT)
    dataframe["payload"] = dataframe.apply(lambda row: row.to_json(), axis=1)

    # Align with Snowflake schema
    dataframe = enforce_snowflake_schema(dataframe, schema["expected_columns"])

    if output_format not in SERIALIZERS:
        raise ValueError(f"Unsupported output format: {output_format}")

    SERIALIZERS[output_format](dataframe, output_directory)
    logger.info(
        "Data transformed and serialized",
        output_format=output_format,
        output_directory=output_directory,
    )
    return f"{output_directory}.{output_format}"
