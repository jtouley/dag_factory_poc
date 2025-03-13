import pandas as pd
import re
import structlog

logger = structlog.get_logger()

def process_txt(file_content):
    """
    Processes text file content and returns a validated DataFrame.
    """
    data = []
    lines = file_content.split("\n")[1:]  # Skip header
    index = 0

    while index < len(lines):
        for _ in range(19):
            if index >= len(lines):
                logger.info("Reached end of file.")
                return pd.DataFrame(data, columns=["Status", "Name", "Card", "Location", "IN/OUT", "Timestamp"])
            
            row = lines[index].strip()
            logger.debug("Processing row", row=row)
            
            match = re.match(r"(Admitted|Rejected \(Clearance\)) '(.+?) \[Default\]' \(Card: (\d+)\)\s+at '(.+?) \[ROK\]' \((IN|OUT)\)\.,(.+)", row)
            
            if match:
                columns = match.groups()
                logger.debug("Parsed columns", columns=columns)
                data.append(columns)
            else:
                logger.warning("Row did not match expected format", row=row)
            
            index += 1
        
        index += 2  # Skip 2 rows
        logger.debug("Skipping 2 rows.")

    return pd.DataFrame(data, columns=["Status", "Name", "Card", "Location", "IN/OUT", "Timestamp"])

def validate_data(df):
    """
    Performs basic validation on the processed DataFrame.
    """
    if df.empty:
        logger.error("Data validation failed: No data found")
        raise ValueError("No data processed. Ensure the S3 file is not empty.")
    
    if df.isnull().values.any():
        logger.error("Data validation failed: NULL values found")
        raise ValueError("Data contains NULL values. Stopping pipeline.")
    
    logger.info("Data validation passed", record_count=len(df))
    return True