import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from kb_builder.pre_processor.video_file_processor import process_video
from kb_builder.vectorize.vectorize import process as vectorize_block

class TestVideoIntegration(unittest.TestCase):

    @patch('kb_builder.pre_processor.video_file_processor.whisper')
    @patch('kb_builder.pre_processor.video_file_processor.VideoFileClip')
    @patch('kb_builder.pre_processor.video_file_processor.os.path.exists')
    @patch('kb_builder.pre_processor.video_file_processor.os.remove')
    @patch('kb_builder.vectorize.vectorize.chunk_and_embed')
    @patch('kb_builder.vectorize.vectorize.SQLite')
    @patch('kb_builder.vectorize.vectorize.HnswlibVectorDB')
    @patch('kb_builder.vectorize.vectorize.sentence_transformer_model')
    def test_video_timestamp_in_region(self, mock_model, mock_vector_db, mock_sqlite, 
                                      mock_chunk_embed, mock_remove, mock_exists, 
                                      mock_video_clip, mock_whisper):
        # Setup video mock
        mock_video = Mock()
        mock_video.duration = 60.0
        mock_audio = Mock()
        mock_audio.write_audiofile = Mock()
        mock_video.audio = mock_audio
        mock_video_clip.return_value = mock_video
        
        mock_exists.return_value = True
        
        # Mock whisper transcription with timestamps
        mock_whisper_model = Mock()
        mock_whisper.load_model.return_value = mock_whisper_model
        mock_whisper_model.transcribe.return_value = {
            'text': 'Full transcript',
            'segments': [
                {'start': 0.0, 'end': 5.5, 'text': ' First segment of video.'},
                {'start': 5.5, 'end': 10.2, 'text': ' Second segment here.'}
            ]
        }
        
        # Mock embedding model
        mock_embedding_model = Mock()
        mock_embedding_model.dim.return_value = 384
        mock_model.return_value = mock_embedding_model
        
        # Mock chunk_and_embed to return the segments as chunks
        mock_chunk_embed.return_value = (
            ["First segment of video.", "Second segment here."],
            [[0.1] * 384, [0.2] * 384]
        )
        
        # Mock SQLite
        mock_db = Mock()
        mock_db.lock.return_value = MagicMock()
        mock_db.insert.side_effect = [1, 2]  # Return chunk IDs
        mock_sqlite.return_value = mock_db
        
        # Mock vector DB
        mock_vdb = Mock()
        mock_vector_db.return_value = mock_vdb
        
        # Process video
        blocks = process_video('/test/video.mp4', '/test/work')
        
        # Verify we got blocks with timestamps
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].region.start_time, 0.0)
        self.assertEqual(blocks[0].region.end_time, 5.5)
        self.assertEqual(blocks[1].region.start_time, 5.5)
        self.assertEqual(blocks[1].region.end_time, 10.2)
        
        # Vectorize the first block
        result = vectorize_block(blocks[0], 'test_video.mp4', 'test_category', 123)
        
        # Verify the region was serialized correctly
        # The insert call should have been made with the region JSON
        insert_calls = mock_db.insert.call_args_list
        self.assertGreater(len(insert_calls), 0)
        
        # Check the region JSON in the insert call
        region_json_arg = insert_calls[0][0][1][3]  # Fourth argument in the SQL insert
        region_data = json.loads(region_json_arg)
        
        # Verify the timestamp data is preserved
        self.assertEqual(region_data['start_time'], 0.0)
        self.assertEqual(region_data['end_time'], 5.5)

if __name__ == '__main__':
    unittest.main() 