from openai import OpenAI
import streamlit as st
from openai import OpenAI
import streamlit as st
import pandas as pd
import os

def chunk_text(text, max_chars=4000):
    """
    Chunk text into chunks of max_chars.
    It makes sure that sentences are not split across chunks.
    Also, adds the last sentence of the previous chunk to the next chunk.
    """

    chunks = []
    chunk = ''
    # Split the text into sentences
    sentences = text.split('.')
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
    return [c for c in chunks if c.strip()]

def convert_text_to_speech(input_text, output_file):
    api_key = st.session_state.openai_key
    # If openai key does not exist, return
    if not api_key:
        return "No OpenAI key found. Unable to convert text to speech."
    client = OpenAI(api_key=api_key)

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=input_text,
    )

    response.stream_to_file(output_file)
    return output_file

def manage_length(text, output_file, max_chars=4000):
    """
    If text is longer than max_chars, chunk it into smaller chunks.
    Then create audio for each chunk and join them together with the final audio file name.
    """
    if len(text) < max_chars:
        convert_text_to_speech(text, output_file)
    else:
        chunks = chunk_text(text, max_chars)
        # Create audio for each chunk
        audio_files = []
        # Create a temp folder with the same name as the output file without the extension
        temp_folder = output_file.replace(".mp3", "")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        for i, chunk in enumerate(chunks):
            st.progress(i/len(chunks), f"Creating audio for chunk {i+1}/{len(chunks)}")
            file_name = os.path.join(temp_folder, f"{i}.mp3")
            convert_text_to_speech(chunk, file_name)
            audio_files.append(file_name)
        # Join the audio files
        join_audio_files(audio_files, output_file)
    return None

def join_audio_files(audio_files, output_file):
    with open(output_file, 'wb') as wfd:
        for f in audio_files:
            with open(f, 'rb') as fd:
                wfd.write(fd.read())
    return output_file

def extract_text_from_parquet(file_name, column_name):
    df = pd.read_parquet(file_name)
    text = "\n".join(df[column_name].to_list())
    return text

def tool_main(file_name=None, column_name=None, text=None, auto_rerun=True):
    """
    This tool converts the given text to speech, saves it to the output file, and plays it.
    It requires source text which can either be a column in a parquet file or a text string.

    Parameters
    ----------
    file_name: str
        The name of the parquet file containing the source text. Can be None if text is provided.
    column_name: str
        The name of the column containing the source text. Can be None if text is provided.
    text: str
        The source text. Can be None if file_name and column_name are provided.
    
    Returns
    -------
    output_file: str
        The name of the file containing the audio.    
    """
    # Create audio folder if it does not exist
    audio_folder = os.path.join(st.session_state.user_folder, "audio")
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)
    # Create a subfolder based on graph name
    graph_name = st.session_state.task_graph.name
    graph_folder = os.path.join(audio_folder, graph_name)
    if not os.path.exists(graph_folder):
        os.makedirs(graph_folder)
    
    # Get the text
    if text is None:
        text = extract_text_from_parquet(file_name, column_name)
    if st.checkbox("Show text being converted", key=f"{file_name}-{column_name}", value=False, help="Check to show the text being converted to speech."):
        st.markdown(text)
    # File name is hash of text without a minus + .mp3 
    file_name = str(hash(text)) + ".mp3"
    # Remove minus sign
    file_name = file_name.replace("-", "")
    # Create full path
    output_file = os.path.join(graph_folder, file_name)
    # Get the audio if it does not exist
    if not os.path.exists(output_file):
        with st.spinner("Creating audio..."):
            manage_length(text, output_file)
    # Play the audio
    st.warning("Audio created. Click play to listen.")
    st.audio(output_file, format="audio/mp3")
    return output_file
