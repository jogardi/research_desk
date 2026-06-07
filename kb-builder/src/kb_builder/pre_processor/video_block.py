from dataclasses import dataclass
from typing import Optional

@dataclass
class VideoRegion:
    """Represents a time range in a video."""
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'start_time': self.start_time,
            'end_time': self.end_time
        }

@dataclass
class VideoBlock:
    """Represents a block of transcribed text from a video with its time range."""
    text: str
    type: str = "transcript"
    region: VideoRegion = None 