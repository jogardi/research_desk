#!/usr/bin/env python3
"""
Example of video processing with timestamp extraction for jump-to-excerpt feature.

This demonstrates how:
1. Videos are transcribed with timestamps using Whisper
2. Video blocks are created with time ranges 
3. The time ranges are stored in the database for later use
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kb_builder.pre_processor.video_file_processor import process_video
from kb_builder.pre_processor.video_block import VideoBlock, VideoRegion

def demo_video_processing():
    """Demonstrate video processing with timestamps"""
    
    # Example of what process_video returns:
    print("=== Video Processing Example ===\n")
    
    # Simulated video blocks that would be returned by process_video
    example_blocks = [
        VideoBlock(
            text="Welcome to our product demonstration.",
            type="transcript",
            region=VideoRegion(start_time=0.0, end_time=5.5)
        ),
        VideoBlock(
            text="Today we'll be showing you the key features.",
            type="transcript", 
            region=VideoRegion(start_time=5.5, end_time=9.2)
        ),
        VideoBlock(
            text="First, let's look at the dashboard interface.",
            type="transcript",
            region=VideoRegion(start_time=9.2, end_time=13.8)
        )
    ]
    
    print("Video blocks created from transcription:\n")
    for i, block in enumerate(example_blocks):
        print(f"Block {i+1}:")
        print(f"  Text: {block.text}")
        print(f"  Time: {block.region.start_time}s - {block.region.end_time}s")
        print(f"  Type: {block.type}")
        print()
    
    # Show how the region is serialized for storage
    import json
    print("How regions are stored in the database:\n")
    for i, block in enumerate(example_blocks):
        region_json = json.dumps(block.region.to_dict())
        print(f"Block {i+1} region JSON: {region_json}")
    
    print("\n=== Key Points ===")
    print("1. Each video segment has precise start/end timestamps")
    print("2. The timestamps enable 'jump to excerpt' functionality in the UI")
    print("3. Video transcripts skip agentic chunking and use sentence splitting")
    print("4. The region data is stored as JSON in the CHUNK table")

if __name__ == "__main__":
    demo_video_processing() 