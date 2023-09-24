def create_new_function_with_llm(system_message, prompt):
    """
    This helps create a new function based on 
    natural language description of what the function should do.

    The function can be saved to views.py for later use.
    """

    info_state = st.empty()
    if st.button("Go GPT!", key='main button'):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        info_state.info("Getting response from GPT")
        response = get_gpt_output(system_message)
        st.session_state.response = response
        info_state.warning("Response received from GPT")    
        func_found = parse_function_from_response()
        if func_found:
            info_state.success("Extracted function from response")
            st.code(st.session_state.the_func, language='python')
        else:
            info_state.error("Could not extract function from response")
            st.code(response, language='python')
    return None

def parse_function_from_response():
    
    # If there are triple backticks, get the function

    # the_func is the first thing between triple backticks, if any
    # If the func is a list, take the first one
    if "```" in st.session_state.response:
        the_func = st.session_state.response.split('```')
        func_found = True
        the_func = the_func[1].strip()
        the_func = clean_function(the_func)
        
    # If we get a response with backticks but has the function
    elif 'my_func' in st.session_state.response:
        func_found = True
        the_func = st.session_state.response.strip()
        the_func = clean_function(the_func)
    else:
        the_func = "None"
        func_found = False
    
    return func_found

def fix_error_in_code():
    """
    Sends the error and the current code to the LLM to fix the error
    """
    prompts.get_prompt_to_fix_error()
    messages = st.session_state.error_messages
    with st.spinner('Fixing an error I ran into...'):
        st.error(f"I got this error: {st.session_state.error}")
        response = gpt_function_calling(messages, functions=funcs_available())

    # If there is a function call, run it first
    if 'last_function_call' in st.session_state:
        call_status = make_function_call(st.session_state.chat_key)
        del st.session_state['last_function_call']
        del st.session_state['error']
        st.toast("Fixed the error.  Rerunning the app...")
        time.sleep(1)
        st.session_state.chat_status.update("Fixed the error.  Rerunning the app...", expanded=False)
        st.experimental_rerun()
    
    # If there is a response, add it to the chat
    if response:
        st.session_state[st.session_state.chat_key].append(
            {'role': 'assistant', 'content': response}
            )
        # Also append it to error messages
        st.session_state.error_messages.append(
            {'role': 'assistant', 'content': response}
            )
        error_prompt = st.chat_input("Type your response to error resolution", key='error_prompt')
        if error_prompt:
            st.session_state[st.session_state.error_messages].append(
                {'role': 'user', 'content': error_prompt}
                )
            # Restart the process that will invoke this function again
            st.experimental_rerun()
    return None