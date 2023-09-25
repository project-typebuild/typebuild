"""
Post POC.
Use this file to get the following:
- Flexible Chunking
- Multi-processing chunks
- Selecting models based on requirement (number of tokens, etc.)
- Let's add a system to select models. 

"""

import multiprocessing


def parallel_process(func, items):
    # Create a multiprocessing pool with the number of available CPUs
    pool = multiprocessing.Pool(processes=4)
    
    # Apply the function to each item in the list using the pool
    results = pool.map(func, items)
    
    # Close the pool to free up resources
    pool.close()
    
    # Return the results in the same order as the input list
    return [result for result in results]


def chunk_text(text, max_chars=None, model_name='gpt-3.5-turbo', chunk_with=None):
    """
    Chunk text into chunks of max_chars.
    """
    # Set max chars, not setting token length as per openai here.
    max_chars_by_model = {
        'gpt-3.5-turbo': 5000,
        'gpt-3.5': 5000,
        'gpt-4': 15000
    }
    if max_chars is None:
        max_chars = max_chars_by_model[model_name]
    chunks = []
    chunk = ''
    if not chunk_with:
        chunk_with = '.'
    # Split the text into sentences
    sentences = text.split(chunk_with)
    # Remove empty sentences
    sentences = [s for s in sentences if s.strip()]
    # Chunk the sentences        
    for s in sentences:
        if len(chunk) + len(s) < max_chars:
            chunk += f"{s}."
        else:
            chunks.append(chunk)
            chunk = f"{s}."
    chunks.append(chunk)
    return chunks   

def get_message(chunk, system_instruction, prompt_prefix=None, prompt_suffix=None):
    if not prompt_prefix:
        prompt_prefix = f"{system_instruction}\nTRANSCRIPT:"
    
    inp = f"{prompt_prefix}\n{chunk}"
    
    if prompt_suffix:
        inp += f"\n{prompt_suffix}"
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": inp}]


def multi_process_text(text, system_instruction, chunk_with=None, prompt_prefix=None, prompt_suffix=None, max_chars=None, model_name='gpt-3.5-turbo'):
    if not max_chars:
        max_chars = 3000
    # Set max tokens globally as 1/3 of max chars
    max_tokens = int(max_chars / 3)
        
    chunks = chunk_text(text, chunk_with=chunk_with)
    out = multi_process_list(
        chunks, 
        system_instruction, 
        prompt_prefix=prompt_prefix, 
        prompt_suffix=prompt_suffix, 
        max_chars=max_chars, 
        model_name=model_name
        )
    return out

def multi_process_list(chunks, system_instruction, prompt_prefix=None, prompt_suffix=None, max_chars=None, model_name='gpt-3.5-turbo'):
    if not max_chars:
        max_chars = 3000
    # Set max tokens globally as 1/3 of max chars
    max_tokens = int(max_chars / 3)

    messages = []
    for chunk in chunks:
        message = get_message(
            chunk, 
            system_instruction=system_instruction, 
            prompt_prefix=prompt_prefix, 
            prompt_suffix=prompt_suffix
            )
        messages.append([message, max_tokens])
    
    results = parallel_process(get_genstudio_chat_with_tokensize, messages)
    return results
