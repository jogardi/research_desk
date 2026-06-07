import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

import torch

from shared.logger import Logger

class TitleGenerator:
    def __init__(self, model_name="fabiochiu/t5-base-medium-title-generation", enable_mps=True): # fabiochiu/t5-small-medium-title-generation
        """
        Initialize the TitleGenerator with a specified model.
        
        Parameters:
        - model_name (str): Name of the model to be used.
        """
        
        # Check if MPS/GPU is available. If not, use CPU.
        print("enable_mps", enable_mps, type(enable_mps))
        device_type = "mps" if torch.backends.mps.is_available() and enable_mps else "cpu"
        #device_type = "cpu" 
        self.device = torch.device(device_type)
        print("using device: ", device_type)
        print("fallback", os.environ["PYTORCH_ENABLE_MPS_FALLBACK"])
        Logger.debug(f"*** Using device: {device_type}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # Move model to MPS/GPU device
        self.model = self.model.to(self.device)

    def generate_title(self, text, p_temperature = .1,text_is_prompt=False):
        """
        Generate a title for the provided text.
        
        Parameters:
        - text (str): The text for which to generate a title.
        
        Returns:
        - str: The generated title.
        """
        prompt_text = f"{text}\n\nTitle:" if not text_is_prompt else text

        # Encode the prompt to tensor of integers using the tokenizer
        inputs = self.tokenizer(prompt_text, return_tensors="pt", max_length=512, truncation=True, padding=True)

        # Move input tensors to MPS device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate output using the model
        outputs = self.model.generate(
            inputs["input_ids"], 
            max_length=64,  # Increased max length to allow for longer titles
            min_length=10,  # Added minimum length to ensure titles aren't too short
            num_beams=8,  # Use beam search to improve quality
            early_stopping=True, # Enable early stopping to prevent overly long titles
            temperature=p_temperature,  # Added temperature to control creativity
            do_sample=True,  # Set do_sample to True for temperature to be effective
            attention_mask=inputs["attention_mask"],
            # top_k=50,  # Added top_k to control diversity
            # top_p=0.5  # Added top_p to control diversity
            # padding="max_length"  # Ensures input is padded if needed
        )
        
        # Move outputs back to CPU for decoding
        outputs = outputs.cpu()

        # Decode the generated ids to text
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the title part after "Title:"
        title = generated_text.strip()
        if ("Title:" in title):
            title = title.split("Title:")[-1].strip()
        
        return title

if __name__ == "__main__":
    # Create an instance of TitleGenerator
    title_gen = TitleGenerator()
    
    # Example text for which we want to generate a title
    text = (
        "limestone blocks. On average these weigh about 2.6 tons, to give a total mass of over 6.3 million tons.43 We can simply marvel at the craftsmanship and technological abilities of these ancient builders, for they not only orientated their monument towards the four cardinal points and kept the plan square and the slopes true, but they cased its four sloping faces with finely polished white limestone from the quarries at Tura on the other side of the Nile. Judging by the few facing stones remaining at the foot of the north side of the pyramid, these were even larger than those used in the core of the building and weighed some fifteen tons each. They were set so closely together that the blade of a knife could not fit between them. The casing-blocks were removed by the Arabs from the thirteenth century (some say to build AD the mosques of Cairo), but when intact the pyramid must have looked even more spectacular than it does today, glittering like a jewel in the sunlight. It is now quite easy to clamber up and down the narrow corridors leading into the pyramids, for banisters are provided and there are wooden ramps with metal footings. The Giza pyramids are also electrically lit inside. Such luxuries were introduced in the 1940s, but exploration was not so easy for earlier travellers, as Ouspensky lamented in 1914: The floor is very slippery; there are no steps, but on the polished stone there are horizontal notches, worn"

    )
    
    # Generate title
    title = title_gen.generate_title(text)
    print("Generated Title:", title)
