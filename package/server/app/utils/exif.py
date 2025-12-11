#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/7 23:23
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-exif.py
@Description : 
"""
import shutil
from datetime import datetime
import re
from typing import Dict, Any, Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json
import reverse_geocoder as rg

from app.utils.filename import extract_datetime_from_filename

# Helper Functions for Metadata

def _convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    """

    def _to_float(v):
        if isinstance(v, (tuple, list)) and len(v) == 2:
            # Handle (numerator, denominator) tuple
            if v[1] == 0:
                return 0.0
            return float(v[0]) / float(v[1])
        try:
            # Handle IFDRational or simple numbers
            return float(v)
        except (TypeError, ValueError):
            # Fallback for IFDRational in some PIL versions if it doesn't cast directly
            if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                if v.denominator == 0:
                    return 0.0
                return float(v.numerator) / float(v.denominator)
            return 0.0

    d = _to_float(value[0])
    m = _to_float(value[1])
    s = _to_float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_gps_info(exif_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    if 'GPSInfo' not in exif_data:
        return None

    gps_info = exif_data['GPSInfo']

    lat = None
    lng = None

    if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat

    if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
        lng = _convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E':
            lng = -lng

    if lat is not None and lng is not None:
        return {"latitude": lat, "longitude": lng}
    return None


def get_exif_data(image: Image.Image) -> Dict[str, Any]:
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                # Filter out binary data or non-serializable stuff if needed
                if isinstance(value, (bytes, bytearray)):
                    try:
                        exif_data[decoded] = value.decode()
                    except:
                        exif_data[decoded] = str(value)
                else:
                    exif_data[decoded] = value
    return exif_data


def extract_metadata(file_path: str, filename: str, image_obj: Optional[Image.Image] = None) -> Dict[str, Any]:
    """
    Extracts photo_time, exif_info, and location from the file.
    Priority:
    1. EXIF DateTimeOriginal
    2. Filename (YYYYMMDD_HHMMSS or YYYYMMDD)
    3. Current Time
    """
    metadata = {
        "photo_time": None,
        "exif_info": None,
        "location": None
    }

    # 1. Try EXIF
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff', '.webp')):
            exif_dict = None
            if image_obj:
                exif_dict = get_exif_data(image_obj)
            else:
                with Image.open(file_path) as img:
                    # Extract full EXIF
                    exif_dict = get_exif_data(img)

            if exif_dict:
                # Serialize for storage
                # Convert non-serializable objects to string
                def default_serializer(obj):
                    if isinstance(obj, (bytes, bytearray)):
                        return str(obj)
                    return str(obj)

                metadata["exif_info"] = json.dumps(exif_dict, default=default_serializer, ensure_ascii=False)

                # Extract Date (DateTimeOriginal)
                date_str = exif_dict.get("DateTimeOriginal")
                if date_str:
                    try:
                        metadata["photo_time"] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        pass

                # Extract GPS
                gps = get_gps_info(exif_dict)
                metadata["location"] = gps
                
                if gps:
                    try:
                        results = rg.search([(gps["latitude"], gps["longitude"])])
                        if results:
                            res = results[0]
                            metadata["location_details"] = {
                                "latitude": gps["latitude"],
                                "longitude": gps["longitude"],
                                "city": res.get("name", ""),
                                "province": res.get("admin1", ""),
                                "country": res.get("cc", ""),
                                "address": f"{res.get('name', '')}, {res.get('admin1', '')}, {res.get('cc', '')}"
                            }
                    except Exception as e:
                        print(f"Reverse geocoding error: {e}")

    except Exception as e:

        print(f"Error extracting metadata: {e}")

    # 2. If photo_time is still None, try Filename
    if metadata["photo_time"] is None:
        try:
            photo_time = extract_datetime_from_filename(filename)
            if photo_time:
                metadata["photo_time"] = photo_time
        except Exception:
            pass

    # 3. Fallback to current time
    if metadata["photo_time"] is None:
        metadata["photo_time"] = datetime.now()

    return metadata

