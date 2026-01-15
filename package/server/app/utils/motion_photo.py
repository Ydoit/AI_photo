import os
import re

def get_video_offset(file_path: str) -> int | None:
    """
    Detects if a file is a Google Motion Photo and returns the video offset (bytes from end).
    Returns None if not a Motion Photo.
    """
    try:
        with open(file_path, 'rb') as f:
            # 1. Check for XMP Metadata (GCamera:MicroVideoOffset)
            # Read the beginning of the file (usually within first 64KB for XMP)
            chunk_size = 64 * 1024
            data = f.read(chunk_size)

            # Pattern for XMP MicroVideoOffset
            # Looks like: GCamera:MicroVideoOffset="12345" or <GCamera:MicroVideoOffset>12345</GCamera:MicroVideoOffset>
            # We look for the attribute/tag and capture the digits

            # Simple regex for MicroVideoOffset
            # We look for the keyword and then some digits
            # Note: XMP can be complex, but usually it's plain text in the header.

            # Case 1: Attribute style
            # xmp:GCamera:MicroVideoOffset="12345"
            match = re.search(b'MicroVideoOffset=["\']?(\\d+)["\']?', data)
            if match:
                return int(match.group(1))

            # Case 2: Tag style
            # <GCamera:MicroVideoOffset>12345</GCamera:MicroVideoOffset>
            match = re.search(b'<[\\w:]*MicroVideoOffset>(\\d+)<', data)
            if match:
                return int(match.group(1))

        # 2. Fallback: Scan for embedded MP4 (ftyp atom)
        # We assume the video is appended to the file.
        # We look for the 'ftyp' atom which marks the start of the video.
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            content = f.read()
            matches = [m.start() for m in re.finditer(b'ftyp', content)]
            
            for pos in matches:
                if pos < 4: continue
                atom_start = pos - 4
                
                # Check if this looks like a valid atom size
                if atom_start + 4 > len(content): continue
                
                size_bytes = content[atom_start:atom_start+4]
                size = int.from_bytes(size_bytes, 'big')
                
                # Sanity check for ftyp atom size (usually small, e.g. 20-32 bytes)
                if 8 <= size <= 128:
                    if atom_start > 0:
                        return file_size - atom_start

            return None

    except Exception:
        return None

def extract_video(file_path: str, offset: int = None, video_path: str = None) -> str | None:
    """
    Extracts the video from a Motion Photo to a separate .mp4 file.
    Returns the path to the extracted video if successful, else None.
    The video is saved with the same basename as the image, but with .mp4 extension.
    If the .mp4 file already exists, it is NOT overwritten, and we return its path.
    """
    if offset is None:
        offset = get_video_offset(file_path)
        if offset is None:
            return None

    if video_path is None:
        video_path = os.path.splitext(file_path)[0] + '.mp4'

    if os.path.exists(video_path):
        return video_path

    try:
        file_size = os.path.getsize(file_path)
        video_start = file_size - offset

        if video_start <= 0 or video_start >= file_size:
            return None

        with open(file_path, 'rb') as f_in:
            f_in.seek(video_start)
            video_data = f_in.read(offset)

            # Verify it looks like a video (check for 'ftyp' or generic binary signature?)
            # MP4 usually starts with size (4 bytes) + 'ftyp'
            # But the embedded stream might not have the header at exactly the offset?
            # Actually, the offset is usually exact.

            # Let's write it.
            with open(video_path, 'wb') as f_out:
                f_out.write(video_data)

        return video_path
    except Exception:
        # If extraction fails, we might want to cleanup
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass
        return None
