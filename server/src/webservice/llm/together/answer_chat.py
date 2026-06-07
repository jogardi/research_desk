from webservice.hparams_config import hpc
from webservice.llm.together.together_chat_completion import TogetherChatCompletion
from webservice.llm.llm_types import ChatRequest, Message

# model="zero-one-ai/Yi-34B"
# model="mistralai/Mistral-7B-v0.1"
# model = "mistralai/Mixtral-8x22B"
# model = "zero-one-ai/Yi-6B"
model = hpc().LLM_MODEL_ANSWER

def generate_answer(user_query: str, text: str, exclude_llm_knowledgebase: bool) -> str:
    
    # Query the language model for the answer
    # estimated_tokens = TogetherChatCompletion.estimated_tokens(text)
    # print(f'Estimated tokens: {estimated_tokens}')
    # estimated_tokens = int(estimated_tokens * 1.05)
    # estimated_tokens = 4096 - estimated_tokens - 100
    # print(f'Max tokens: {estimated_tokens}')
    
    prompt = ""
    if exclude_llm_knowledgebase:
        prompt = hpc().EXCLUDE_LLM_TRAINING_DATA_INSTRUCTIONS
    else:
        prompt =  "Use the following text as context when answering user queries"

    messages = [
        { "role": "system", "content": f"{prompt}:\n\n{text}" },
        { "role": "user", "content": user_query},
    ]

    chat_request: ChatRequest = { 
        "model": model, 
        "messages": messages, 
        #"max_tokens": 1000, 
        "temperature": 0.1, 
        "top_p": 0.7, 
        "top_k": 50, 
        "repetition_penalty": 1.1
    }

    message, error_response = TogetherChatCompletion.query(chat_request)
    
    if error_response is not None:
        return None, error_response
    
    if ('error' in message):
        print(f"*** ERROR: {message['error']['type']}")
        if ('message' in message['error'] and message['error']['type'] == 'invalid_request_error'):
            raise Exception('invalid_request_error')

    return message["content"], None

if __name__ == "__main__":
    text = "reigned a thousand years after Khafre and Khufu, and cautioned that “we are building our hypothesis on New Kingdom texts which were written at a time when the Egyptians themselves had probably forgotten the original traditions of the God [Sphinx] . . . it is more than probable that neither Thothmes IV nor the priesthood attached to the Sphinx (if, indeed it had a priesthood at that time), knew the truth of the origin of the statue” (Hassan 1953, 12). Stadelmann took the same position as Hassan and finally was compelled to conclude that “as there is no clear philological ascertainment for the creator of the Great Sphinx, we have to look for archaeological ones” (Stadelmann 2000, 465; Hassan 1953, 152). We agree with Hassan and Stadelmann on this matter. Neither the inscription on the Great Limestone Stela of Amenhotep II nor that on the Dream Stela of his son, Tuthmoses IV, can be used as “proof” that the Sphinx was created by a Fourth-Dynasty pharaoh. Indeed, if we are to go by the inscriptions, then we should conclude that the Sphinx was already in existence long before the Fourth Dynasty! For there is, in fact, a “clear philological ascertainment” on the Dream Stela itself that tells us in no uncertain terms that the Sphinx had been in existence since the remote “first time,” that is, zep tepi—a time that in the mind of the ancient Egyptians harked back to a very distant epoch when the “gods” ruled Egypt.\n\nabout 40 feet high—was erected at Huaca Prieta sometime between circa 3000 and 2600 B.C. Recent excavations of yet another site in a remote Peruvian valley have revealed an even more impressive set of pyramids surrounded by the oldest known city in the New World, dated to as early as 2627 B.C. Called Caral and located in the Supe Valley, about 14 miles from the coast, the 170-acre site centered around a huge, sunken circular plaza over one third of a mile across and surrounded by large stepped pyramids. The largest of the pyramids stands 65 feet tall and covers an area larger than a football field. The dwellings of Caral’s elite, made of stone with large rooms and plaster walls, were built close to the pyramids, whereas lower-class dwellings, constructed from mud and cane, lay farther out, closer to the edges of the city. Like the pyramids at Aspero and El Paraíso, those at Caral were made of rubble and stone carried in woven reed bags and piled up behind retaining walls. We know almost nothing beyond the fact that these ancient people constructed the earliest monumental pyramids. Exactly who these people were or why they built these curious and fascinating structures remains an unanswered and potentially very important question.\n\n13 Ibid. 14 Ibid. The ‘White Wall’ probably refers to the Tura limestone walls of the royal palace and the boundary wall of Memphis. 15 Ibid., p. 54. 16 Most Egyptologists would contest this point, but we feel that the evidence is overwhelming in favour of a direct cultic connection between Osiris and the Great Pyramid. An interesting article touching upon this idea can be read in Steuart Campbell, ‘The Origin and Purpose of the Pyramids’ in the New Humanist, December 1990 issue, pp. 3-4, who wrote that ‘the Great Pyrami d might have been intended as a dwelling place for the spirit of Osiris’. The French Antiquarian and Freemason, Alexandre Lenoir (see ‘A dissertation on the Pyramids of Egypt’ in FMR No. 39, 1989) was also to claim that ‘all considered it [the Great Pyramid] may be the tomb of Osiris’.\n\nlike a divinity guarding the dead. ROCHFORT SCOTT (1837) Rambles in Egypt and Candia . . . (London: 1837), 2 vols. Vol. 1, page 242 In the face of the scarped rock, about a quarter of a mile to the south of the great pyramids, is a Hypogean temple, the entrance of which is also decorated with figures and hieroglyphics. The Arab guides were averse to my entering it. . . . The great Sphynx is to the eastward of this temple; no part of it but the head could be seen, the sand drifts so constantly upon it. It stands on a much lower level than the pyramids. SIR WILLIAM WILDE (1837) Narrative of a Voyage to Madeira . . . Egypt . . . and Greece (Dublin: 1840), 2 vols. Page 393 A line of camels slowly pacing across the dreary waste, on which they [the pyramids] stand, or a Bedawee [Bedouin] careering his horse beside the base, give, by comparison, some faint idea of their [the pyramids’] stupendous size, and an Arab pirouetting his charger on the sphinx *3 afforded me the desired contrast, at the same time that it showed me what was the magnitude of that emblem of Egyptian reverence and superstition.\n\n"
    answer, error_response = generate_answer(text)
    if error_response is not None:
        print(f"Failed to generate answer: {error_response}")
    else:
        print(answer)
        print('-'*50)
        print(text)




