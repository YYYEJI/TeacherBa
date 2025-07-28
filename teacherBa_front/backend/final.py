from dotenv import load_dotenv
import os
from glob import glob

from pprint import pprint
import json

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.tools import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from IPython.display import Image, display
from typing import TypedDict, Literal

load_dotenv()

# LLM 세팅
llm = AzureChatOpenAI(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0
)

embeddings_model = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=1024,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

# 상태
class State(TypedDict):   # TypeDict 클래스에서 상속받아 정의, state: 각 단계별로 정도 넘김
    input_message: str    # query
    final_answer: str     # 최종 답변

# Identify_query (A)
def identify_query(state: State):
    prompt = f"""다음 질문이 운전 관련된 질문인지 파악해주세요. 
정확히 "운전 관련" 또는 "운전 질문"이라고만 답해주세요.

[질문]
{state['input_message']}

[답변]
"""
    response = llm.invoke(prompt)
    print("[DEBUG identify_query 응답]", response.content)

    if "운전" in response.content:
        return Command(goto="identify_low_or_maintenance")
    else:
        print("운전 관련 질문만 해주세요!")
        return None


# Identify_Law_or_Maintenance_or_general (B)
def identify_low_or_maintenance(state: State):
    prompt = f"""다음 질문이 운전법규/차량정비 관련 질문인지 아닌지 파악해주세요:

    [질문]
    {state['input_message']}

    [답변]
    """
    response = llm.invoke(prompt)
    if "운전법규" in response.content:
        return Command(goto="traffic_law")
    elif "정비" in response.content:
        return Command(goto="car_maintanance")
    else:
        return Command(goto="traffic_general")

# Traffic_Law (c)
def traffic_law(state: State) -> Command[Literal[END]]:
    chroma_db = Chroma(
        persist_directory="./db_trafficLaw",
        embedding_function=embeddings_model
    )
    retriever = chroma_db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k":10,"lambda_mult": 0.4},
    )
    template = """주어진 컨텍스트를 기반으로 질문에 답변하시오.
    [지침]
    - 컨텍스트에 있는 정보만을 사용하여 답변할 것
    - 불확실한 경우 명확히 그 불확실성을 표현할 것
    - 답변은 논리적이고 구조화된 형태로 제공할 것
    - 답변은 한국어를 사용할 것
    [컨텍스트]
    {context}
    [질문]
    {question}
    [답변]
    """
    prompt = ChatPromptTemplate.from_template(template)

    # 문서 포맷팅
    def format_docs(docs):
        return "\n\n".join([getattr(doc, "page_content", str(doc)) for doc in docs])

    # Rag 체인 생성
    rag_chain = (
        RunnableParallel({
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }) | prompt | llm | StrOutputParser()
    )
    
    # 체인 실행
    query = state["input_message"]
    output = rag_chain.invoke(query)
    
    # 상태 업데이트와 함께 다음 노드로 라우팅
    return Command(goto=END, update={"final_answer": output})

# Traffic_maintanance
def car_maintanance(state: State) -> Command[Literal[END]]:
    tool = TavilySearchResults(
        max_result=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
    )

    template = """다음은 차량 정비 관련 질문에 대한 답변입니다. 주어진 컨텍스트를 기반으로 논리적으로 답변해주세요.

    [지침]
    - 컨텍스트에 있는 정보만을 바탕으로 답변할 것
    - 확실하지 않은 정보는 명확하게 언급할 것
    - 한국어로 답변할 것

    [컨텍스트]
    {context}

    [질문]
    {question}

    [답변]
    """

    prompt = ChatPromptTemplate.from_template(template)
    
    # 문서 포매팅
    def format_docs(docs):
        return "\n\n".join([
            doc.page_content if hasattr(doc, "page_content") 
            else doc.get("content", str(doc)) 
            for doc in docs
        ])
        
    # RAG 체인 생성
    rag_chain = (
        RunnableParallel({
            "context": tool | format_docs,
            "question": RunnablePassthrough()
        }) | prompt | llm | StrOutputParser()
    )

    # 체인 실행
    query = state["input_message"]
    output = rag_chain.invoke(query)

    # 상태 업데이트와 함께 다음 노드로 라우팅
    return Command(goto=END, update={"final_answer": output})

# Traffic_general (E)
def traffic_general(state: State) -> Command[Literal[END]]:
    tool = TavilySearchResults(
        max_result=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=True
    )
    template = """주어진 컨텍스트를 기반으로 질문에 답변하시오.
    [지침]
    - 컨텍스트에 있는 정보만을 사용하여 답변할 것
    - 불확실한 경우 명확히 그 불확실성을 표현할 것
    - 답변은 논리적이고 구조화된 형태로 제공할 것
    - 답변은 한국어를 사용할 것
    [컨텍스트]
    {context}
    [질문]
    {question}
    [답변]
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # 문서 포매팅
    def format_docs(docs):
        return "\n\n".join([getattr(doc, "page_content", str(doc)) for doc in docs])

    # RAG 체인 생성
    rag_chain = (
        RunnableParallel({
            "context": tool | format_docs,
            "question": RunnablePassthrough()
        }) | prompt | llm | StrOutputParser()
    )
    
    # 체인 실행
    query = state["input_message"]
    output = rag_chain.invoke(query)
    # 상태 업데이트와 함께 다음 노드로 라우팅
    return Command(goto=END, update={"final_answer": output})

# Workflow
# 워크플로우 구성
workflow = StateGraph(State)

# 노드 추가
workflow.add_node("identify_query", identify_query)
workflow.add_node("identify_low_or_maintenance", identify_low_or_maintenance)
workflow.add_node("traffic_law", traffic_law)
workflow.add_node("car_maintanance", car_maintanance)
workflow.add_node("traffic_general", traffic_general)
workflow.add_edge(START, "identify_query")
graph = workflow.compile()

# 실행 함수 (Flask 연동)
def run_agent(user_input: str) -> str:
    initial_state = {"input_message": user_input}
    final_answer = ""

    for output in graph.stream(initial_state, stream_mode="values"):
        if "final_answer" in output:
            final_answer = output["final_answer"]

    return final_answer


## 테스트 실행
# if __name__ == "__main__":
#     text = input("질문을 입력하세요: ")
#     initial_state = {"input_message": text}
#     for chunk in graph.stream(initial_state, stream_mode="values"):
#         pprint(chunk)
#         print("=" * 80)
