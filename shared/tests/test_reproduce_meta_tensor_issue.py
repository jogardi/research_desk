import unittest
import os
import torch
from unittest.mock import patch, MagicMock, Mock
import sys


class TestReproduceMetaTensorIssue(unittest.TestCase):
    """
    Test suite to understand and reproduce the meta tensor issue.
    
    The error "Cannot copy out of meta tensor; no data!" occurs when:
    1. A PyTorch model is loaded with meta tensors (placeholders without actual data)
    2. The model is then moved to a device using .to(device)
    
    Meta tensors can be created in several ways:
    - Using device_map='auto' with transformers
    - Using low_cpu_mem_usage=True
    - Loading models within torch.device('meta') context
    - When accelerate library is misconfigured
    """

    def test_demonstrate_meta_tensor_error(self):
        """Demonstrate how meta tensor error occurs with a simple example"""
        import torch.nn as nn
        
        # Create a model with meta tensors
        class MetaModel(nn.Module):
            def __init__(self):
                super().__init__()
                with torch.device('meta'):
                    self.linear = nn.Linear(768, 1024)
            
            def forward(self, x):
                return self.linear(x)
        
        model = MetaModel()
        
        # Verify it has meta tensors
        param = next(model.parameters())
        self.assertTrue(param.is_meta, "Model should have meta tensors")
        
        # Try to move to CPU - this will fail
        with self.assertRaises(NotImplementedError) as cm:
            model.to('cpu')
        
        self.assertIn("Cannot copy out of meta tensor", str(cm.exception))
        print("✅ Successfully demonstrated meta tensor error")

    def test_check_current_model_state(self):
        """Check if the current BGE-M3 model loads with meta tensors"""
        try:
            from FlagEmbedding import BGEM3FlagModel
            
            # Create model normally
            model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
            
            # Check if model has meta tensors
            if hasattr(model, 'model'):
                try:
                    param = next(model.model.parameters())
                    print(f"Model loaded on device: {param.device}")
                    print(f"Has meta tensors: {param.is_meta}")
                    
                    if param.is_meta:
                        print("⚠️  Model loaded with meta tensors! This will cause issues.")
                    else:
                        print("✅ Model loaded normally without meta tensors")
                except StopIteration:
                    print("No parameters found in model")
                    
        except Exception as e:
            print(f"Error checking model state: {e}")

    def test_patch_bgem3_to_force_meta_tensors(self):
        """Force BGE-M3 to load with meta tensors by patching its initialization"""
        from FlagEmbedding import BGEM3FlagModel
        
        # Create a mock that simulates a model with meta tensors
        original_init = BGEM3FlagModel.__init__
        
        def patched_init(self, model_name_or_path, *args, **kwargs):
            # Call original init
            original_init(self, model_name_or_path, *args, **kwargs)
            
            # Replace the model with one that has meta tensors
            if hasattr(self, 'model'):
                # Create a mock model that will fail when moved to device
                mock_model = Mock()
                
                def mock_to(device):
                    raise NotImplementedError(
                        "Cannot copy out of meta tensor; no data! Please use torch.nn.Module.to_empty() "
                        "instead of torch.nn.Module.to() when moving module from meta to a different device."
                    )
                
                mock_model.to = mock_to
                mock_model.device = torch.device('meta')
                
                # Replace the model
                self.model = mock_model
        
        # Patch and test
        BGEM3FlagModel.__init__ = patched_init
        try:
            from shared.embedding.flag_embed import FlagMultiVecEmbedder
            
            embedder = FlagMultiVecEmbedder("BAAI/bge-m3")
            
            with self.assertRaises(NotImplementedError) as cm:
                embedder.emb_query("hello world")
            
            self.assertIn("Cannot copy out of meta tensor", str(cm.exception))
            print("✅ Successfully reproduced meta tensor error with patched model")
            
        finally:
            # Restore original
            BGEM3FlagModel.__init__ = original_init

    def test_diagnose_server_environment(self):
        """Diagnose potential causes of meta tensors in server environment"""
        
        print("\n=== Diagnosing Environment ===")
        
        # Check environment variables that might affect model loading
        env_vars = [
            'CUDA_VISIBLE_DEVICES',
            'TRANSFORMERS_OFFLINE', 
            'HF_HUB_OFFLINE',
            'ACCELERATE_USE_CPU',
            'ACCELERATE_MIXED_PRECISION',
            'ACCELERATE_CONFIG_FILE',
            'HF_HUB_DISABLE_TQDM',
            'PROFILE'
        ]
        
        print("\nEnvironment variables:")
        for var in env_vars:
            value = os.environ.get(var, '<not set>')
            print(f"  {var}: {value}")
        
        # Check if accelerate is installed and its configuration
        try:
            import accelerate
            print(f"\nAccelerate version: {accelerate.__version__}")
            
            # Check for accelerate config
            from pathlib import Path
            config_path = Path.home() / '.cache' / 'huggingface' / 'accelerate' / 'default_config.yaml'
            if config_path.exists():
                print(f"Accelerate config exists at: {config_path}")
                print("This might affect model loading behavior")
        except ImportError:
            print("\nAccelerate not installed")
        
        # Check transformers cache
        try:
            from transformers.utils import TRANSFORMERS_CACHE
            print(f"\nTransformers cache: {TRANSFORMERS_CACHE}")
            cache_path = Path(TRANSFORMERS_CACHE)
            if cache_path.exists():
                bge_models = list(cache_path.glob("**/models--BAAI--bge-m3"))
                if bge_models:
                    print(f"BGE-M3 cached at: {bge_models[0]}")
        except:
            pass
        
        # Check PyTorch configuration
        print(f"\nPyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")

    def test_workaround_for_meta_tensor_issue(self):
        """Test potential workarounds for the meta tensor issue"""
        
        print("\n=== Testing Workarounds ===")
        
        # Workaround 1: Clear caches
        print("\n1. Clearing model caches...")
        from shared.embedding.sentence_transformer import sentence_transformer_model
        if hasattr(sentence_transformer_model, 'cache_clear'):
            sentence_transformer_model.cache_clear()
            print("   ✓ Cleared sentence_transformer_model cache")
        
        # Workaround 2: Force CPU device
        print("\n2. Testing with forced CPU device...")
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            try:
                from shared.embedding.sentence_transformer import SentenceTransformerModel
                model = SentenceTransformerModel(model="flag/BAAI/bge-m3")
                dim = model.dim()
                print(f"   ✓ Model loaded successfully with dimension: {dim}")
            except Exception as e:
                print(f"   ✗ Still failed: {e}")
        
        # Workaround 3: Check if model files are corrupted
        print("\n3. Checking model file integrity...")
        try:
            from transformers import AutoModel
            # Try loading the base transformer model directly
            model = AutoModel.from_pretrained("BAAI/bge-m3", use_auth_token=False)
            print("   ✓ Base model loads correctly")
            del model  # Clean up
        except Exception as e:
            print(f"   ✗ Base model load failed: {e}")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2) 