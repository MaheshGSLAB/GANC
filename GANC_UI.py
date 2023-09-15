import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationTokenBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import ConversationChain
from ssh_commands import get_ssh_cmd_output
from PIL import Image
import config
import os

CMD_WAIT = 2
host = config.HOST
user = config.USER
password = config.PASSWORD
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY

if 'clicked' not in st.session_state:
    st.session_state.clicked = False


def get_command_output(host, user, password, config_cmds, cmd_wait=CMD_WAIT):
    st.divider()
    st.markdown(f"<h5>Command execution result</h5>",unsafe_allow_html=True)
    output = get_ssh_cmd_output(host, user, password, config_cmds, cmd_wait=CMD_WAIT)
    for out in output.split('\n'):
        st.write(out)
    
    st.divider()
    release_click()


def clicked():
    st.session_state.clicked = True


def release_click():
    st.session_state.clicked = False


def data_reader(file_path):
    file = open(file_path, "r+")
    data = eval(f"[{file.read()}]")

    return data


# LLM
@st.cache_resource
def model():
    llm = ChatOpenAI()
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are a helpful assistant which gives configuration commands for Arista EOS devices."
            ),
            # The `variable_name` here is what must align with memory
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ]
    )
    memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=2000, memory_key="chat_history", return_messages=True, input_key="input")

    training_msg = data_reader("./train.json")
    for i in range(1, len(training_msg)-1, 2):
        memory.save_context({"input": training_msg[i]["content"]}, {"output": training_msg[i+1]["content"]})

    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt
    )

    return conversation


conversation = model()
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
""",unsafe_allow_html=True)

image = Image.open('artifacts/logo.png')

col1, col2, col3 = st.columns(3)

with col1:
    st.write("")
with col2:
    st.image(image)
with col3:
    st.write("")
st.header("Generative AI for vendor: Arista", divider='rainbow')
st.write()
st.markdown(f"<h4>Enter configuration problem</h4>",unsafe_allow_html=True)
user_query = st.text_area("Enter configuration problem", '', label_visibility="collapsed", placeholder="Hi! How may I assist you?")
if user_query:
    response = conversation.predict(input=user_query)
    print(response)
    if "apologize" in response or "confusion" in response or "sorry" in response or "Apologies" in response:
        st.warning("Please check your input query. It seems to be incorrect!", icon='⚠')
    else:
        st.write('Configuration command for the above problem is:')
        st.divider()
        config_cmds = response.split('\n')
        end_index = -1
        for i in range(len(config_cmds)):
            if 'enable' in config_cmds[i]:
                start_index = i
                break
        
        for i in range(start_index, len(config_cmds)):
            if '```' in config_cmds[i]:
                end_index = i
                break

        if end_index == -1:
            config_cmds = config_cmds[start_index:]
        else:
            config_cmds = config_cmds[start_index:end_index]
        for i in config_cmds:
            st.write(f"`{i.strip('AI: ')}`")

        st.divider()

        st.markdown(f"<h4>Want to push the commands on Arista EOS device</h4>",unsafe_allow_html=True)
        pushed = st.button("Execute commands", on_click=clicked)
        if st.session_state.clicked:
            config_cmd = [cmd.strip('AI: ')+"\n" for cmd in config_cmds]
            get_command_output(host, user, password, config_cmd, cmd_wait=CMD_WAIT)
else:
    st.divider()
    