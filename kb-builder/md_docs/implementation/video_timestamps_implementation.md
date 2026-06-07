# Video Timestamp Implementation for Jump-to-Excerpt Feature

## Overview
This implementation adds support for video timestamps in the KB builder, enabling the "View Excerpt on Source Page" feature to work with video search results. When users click this option, the video will display and automatically jump to the time of the excerpt.

## Implementation Details

### 1. New Data Structures

#### VideoRegion (video_block.py)
```python
@dataclass
class VideoRegion:
    """Represents a time range in a video."""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
```

#### VideoBlock (video_block.py)
```python
@dataclass 
class VideoBlock:
    """Represents a block of transcribed text from a video with its time range."""
    text: str
    type: str = "transcript"
    region: VideoRegion
```

### 2. Video Processing Changes

The `process_video` function in `video_file_processor.py` now:
- Uses `whisper.transcribe()` with `word_timestamps=True` to get timestamp information
- Creates `VideoBlock` objects instead of `PDFBlock` objects
- Each block contains the transcribed text and its time range
- Falls back to using the full video duration if segments aren't available

### 3. Chunking Behavior

Video transcripts are handled specially in `chunk_and_embed.py`:
- They always use sentence splitting, even when agentic chunking is enabled
- This ensures consistent, predictable chunking for video content
- The `block_type == 'transcript'` check triggers this special handling

### 4. Database Storage

The timestamp information is stored in the CHUNK table's REGION column as JSON:
```json
{
    "start_time": 0.0,
    "end_time": 5.5
}
```

### 5. Compatibility

The implementation maintains backward compatibility:
- Both `PDFBlock` and `VideoBlock` types are handled in `vectorize.py`
- The region serialization detects the type and uses appropriate serialization
- Existing PDF processing remains unchanged

## Testing

The implementation includes comprehensive tests:
- `test_video_processing.py`: Tests video block creation with timestamps
- `test_video_chunking.py`: Tests that video transcripts skip agentic chunking
- `test_video_integration.py`: Integration test showing the full flow

## Example Usage

```python
from kb_builder.pre_processor.video_file_processor import process_video

# Process a video file
blocks = process_video("path/to/video.mp4", "work_folder")

# Each block contains timestamp information
for block in blocks:
    print(f"Text: {block.text}")
    print(f"Time: {block.region.start_time}s - {block.region.end_time}s")
```

## Next Steps

The UI team can use the timestamp information in the region field to implement the video jump functionality. When a user clicks "View Excerpt on Source Page" for a video result, the UI should:
1. Load the video player
2. Parse the region JSON to get start_time
3. Seek the video to that timestamp
4. Optionally highlight or display the time range 