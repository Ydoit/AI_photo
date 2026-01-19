from fastapi import APIRouter
import aiohttp
from app.core.config_manager import config_manager, VERSION
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.
    Returns:
        1 if v1 > v2
        -1 if v1 < v2
        0 if v1 == v2
    """
    if not v1 or not v2:
        return 0
    try:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        
        length = max(len(parts1), len(parts2))
        parts1.extend([0] * (length - len(parts1)))
        parts2.extend([0] * (length - len(parts2)))
        
        for i in range(length):
            if parts1[i] > parts2[i]:
                return 1
            if parts1[i] < parts2[i]:
                return -1
    except ValueError:
        logger.warning(f"Invalid version format: v1={v1}, v2={v2}")
    return 0

@router.get("/version")
def get_version():
    return {"version": VERSION}

@router.get("/update-check")
async def check_update():
    current_version = VERSION
    update_url = "https://trailsnap.cn/version.json"
    # update_url = "http://localhost:5173/version.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(update_url, timeout=5) as response:
                if response.status == 200:
                    remote_data = await response.json()
                    # sort by version
                    remote_data.sort(key=lambda x: x["version"], reverse=True)
                    remote_version = remote_data[0]["version"]
                    update_info = remote_data[0].get("update_info")
                    download_url = remote_data[0].get("download_url")
                    has_update = compare_versions(remote_version, current_version) > 0
                    update_info = ""
                    for item in remote_data:
                        if compare_versions(item["version"], current_version) > 0:
                            update_info += f"<br>{item['version']}:<br>{item['update_info']}<br>"
                    update_info = update_info.strip().strip("<br>")
                    return {
                        "current_version": current_version,
                        "latest_version": remote_version,
                        "has_update": has_update,
                        "update_info": update_info,
                        "download_url": download_url
                    }
                else:
                     logger.error(f"Update check failed with status: {response.status}")
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
    
    return {
        "current_version": current_version,
        "latest_version": None,
        "has_update": False,
        "error": "Failed to check for updates"
    }
