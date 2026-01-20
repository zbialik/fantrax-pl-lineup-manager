from datetime import datetime
import os
import json
from dataclasses import asdict
import logging
from typing import Any

logger = logging.getLogger(__name__)

def write_datatype_to_json(data: Any, data_dir: str = "data") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    os.makedirs(data_dir, exist_ok=True)
    
    if isinstance(data,list):
        if len(data) > 0:
            datatype = type(data[0]).__name__.lower()
            filename = os.path.join(data_dir, f"list_{datatype}_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump([asdict(d) for d in data], f, indent=2)
        else:
            logger.warning(f"No data to write to filesystem.")
            return
    else:
        datatype = type(data).__name__.lower()
        filename = os.path.join(data_dir, f"{datatype}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(asdict(data), f, indent=2)
    logger.info(f"Saved data to {filename}")
