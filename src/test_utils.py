import shutil
import json
import os
from pathlib import Path
import allure
import random
from typing import Any, Dict, List, Tuple, Union
from browser_use import AgentHistoryList

BASE_64_PLACEHOLDER: str = "BASE_64_PLACEHOLDER"

def replace_base64_in_dict(d: Union[Dict[str, Any], List[Any], Any]) -> Union[Dict[str, Any], List[Any], Any]:
    if isinstance(d, dict):
        return {f"screenshot_{random.randint(1000, 9999)}" if k == 'screenshot' else k: BASE_64_PLACEHOLDER if k == 'screenshot' else replace_base64_in_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [replace_base64_in_dict(item) for item in d]
    return d

def setup_directories(logs_dir: Union[str, Path], steps_dir: Union[str, Path]) -> Tuple[Path, Path]:
    # Ensure paths are absolute
    logs_path = Path(logs_dir)
    steps_path = Path(steps_dir)

    if logs_path.exists():
        shutil.rmtree(logs_path)
    logs_path.mkdir(parents=True, exist_ok=True)

    if steps_path.exists():
        shutil.rmtree(steps_path)
    steps_path.mkdir(parents=True, exist_ok=True)
    return logs_path, steps_path

def save_agent_history(history: AgentHistoryList, logs_dir: Union[str, Path], filename: str = "agent_history.json") -> Dict[str, Any]:
    # Use AgentHistoryList's built-in serialization
    if hasattr(history, 'model_dump'):
        formatted_history = history.model_dump()
    else:
        formatted_history = [
            {k: v for k, v in step.items() if k != 'screenshot'}
            for step in history
            if isinstance(step, dict)
        ]
    
    # Replace base64 strings with placeholder
    formatted_history = replace_base64_in_dict(formatted_history)
    
    file_path = Path(logs_dir) / filename
    with open(file_path, "w") as history_file:
        json.dump(formatted_history, history_file, indent=4, ensure_ascii=False)
    return formatted_history

def attach_logs_to_allure(logs_dir: Union[str, Path]) -> None:
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return
    
    # Get all files and sort them by _[index]
    files: List[Tuple[int, Path]] = []
    for file_path in logs_path.rglob("*"):
        if file_path.is_file():
            # Only process files that match the pattern _[index].txt
            filename = file_path.stem
            if '_' in filename:
                try:
                    # Extract index from filename (e.g., "log_1" -> 1)
                    index = int(filename.split('_')[-1])
                    if file_path.suffix == '.txt':
                        files.append((index, file_path))
                except ValueError:
                    continue
    
    # Sort files by index
    files.sort(key=lambda x: x[0])
    
    # Attach files in sorted order
    for _, file_path in files:
        relative_path = file_path.relative_to(logs_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            allure.attach(
                content,
                name=f"Log: {relative_path}",
                attachment_type=allure.attachment_type.TEXT
            )

def attach_gifs_to_allure(logs_dir: Union[str, Path]) -> None:
    """
    Attach all .gif files in logs_dir to the Allure report.
    """
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return

    for gif_path in logs_path.rglob("*.gif"):
        if gif_path.is_file():
            relative_path = gif_path.relative_to(logs_path)
            with open(gif_path, "rb") as f:
                content = f.read()
                allure.attach(
                    content,
                    name=f"GIF: {relative_path}",
                    attachment_type=allure.attachment_type.GIF
                )

def attach_agent_history_to_allure(logs_dir: Union[str, Path], filename: str = "agent_history.json") -> None:
    """
    Attach agent_history.json to the Allure report if it exists.
    """
    logs_path = Path(logs_dir)
    file_path = logs_path / filename
    if file_path.exists() and file_path.is_file():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            allure.attach(
                content,
                name=f"Agent History: {filename}",
                attachment_type=allure.attachment_type.JSON
            )