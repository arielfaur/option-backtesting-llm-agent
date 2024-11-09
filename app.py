import streamlit as st
import os
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

from llama_index.core import SQLDatabase
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)
from llama_index.core.indices.struct_store.sql_query import NLSQLRetriever
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.agent import ReActAgent
from sqlalchemy import create_engine

os.environ["NVIDIA_API_KEY"]= st.secrets.NVIDIA_API_KEY

st.set_page_config(page_title="Chat with the Streamlit docs, powered by LlamaIndex", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Chat with the Streamlit docs, powered by LlamaIndex 💬🦙")
st.info("Check out the full tutorial to build this app in our [blog post](https://blog.streamlit.io/build-a-chatbot-with-custom-data-sources-powered-by-llamaindex/)", icon="📃")

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "I'm a financial assistant with option trading knowledge. Let me know how I can assist you.",
        }
    ]

def create_db_objectindex():
    schema = """
        quote_date:	date of quote in a readable form (year-month-day) [yyyy-mm-dd]
        type: type of contracts (call or put) [C/P]
        underlying_last:	last price of underlying asset
        expire_date:	expiry date of contract in a readable form (year-month-day) [yyyy-mm-dd]
        dte:	days till expiry
        delta:	delta of option
        gamma:	gamma of option
        vega:	vega of option
        theta:	theta of option
        rho:	rho of option
        iv:	implied volatility of option
        volume:	days traded volume of option
        last:	last traded price of option
        size:	current size of option
        bid:	bid price of option
        ask:	ask price of option
        strike:	option strike price
        strike_distance:	distance between strike price and current underlying price
        strike_distance_pct:	distance as a percentage between strike price and current underlying price
    """

    tables = [
        {
            "table_name": "nvda",
            "context": f"""
                Historical NVIDIA (NVDA) option contracts for the year 2023.
                
                Table schema:
                {schema}
            """
        },
        {
            "table_name": "spx",
            "context": f"""
                Historical S&P 500 (SPX) option contracts for the year 2023.
                
                Table schema:
                {schema}
            """
        }
    ]

    table_schema_objs = [
        (SQLTableSchema(table_name=table["table_name"], context_str=table["context"]))
        for table in tables
    ]   
    
    # define SQL schema, model and create index
    engine = create_engine("sqlite:///data/options.db", echo=True)
    
    sql_database = SQLDatabase(engine, include_tables=[table["table_name"] for table in tables])
    table_node_mapping = SQLTableNodeMapping(sql_database)
    obj_index = ObjectIndex.from_objects(
        table_schema_objs,
        table_node_mapping,
        VectorStoreIndex,
    )

    return sql_database, obj_index
    

def get_prompt_context():
    context = f"""
        You are a financial expert and a trading assistant. Your job is to simulate different options trading strategies on the S&P 500 index (SPX) and NVIDIA (NVDA) stock,
        by calculating the profit/loss of a given trade. You must calculate the profit comparing the premium paid or collected on the date of the trade with the premium 
        paid or collected at expiration date in order to close the trade.
        Do NOT make up option prices, use ONLY the tool to retrieve SPX or NVDA options historical data. If no data is available, inform the user about it.
        Do NOT go off-topic. Respond only to queries about options trading and general information about NVIDIA or the S&P 500 index.
        Always append a semicolon (;) at the end of a SQL query.
        Always explain the steps performed to arrive at a conclusion.

        Here are a few examples:

        1. 1dte long strategy on NVIDIA
        
        Question: Calculate the profit/loss on a 1dte long call option with expiration date March 17th 2023 and a delta between 0.2 and 0.3.
        
        Thought:  I need to find all 1dte call option contracts with the given delta using the NVDA tool. 
        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last
            FROM nvda o
            WHERE o.type = 'C' 
            and o.expire_date = '2023-03-17' 
            AND o.delta BETWEEN 0.20 AND 0.30
            AND o.dte = 1;

        Observation: The delta for this option contract is 0.25698 and strike price is $260. The premium paid for this contract is $1.09 (last traded price).

            
        Thought: I will calculate profit/loss at expiration date (assuming a buy-and-hold strategy). I need to use the NVDA tool to run a SQL query to obtain the call option price at expiration date.
        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last
            FROM nvda o
            WHERE o.type = 'C' 
            and o.expire_date = '2023-03-17' 
            and strike = 260
            AND o.dte = 0;

        Observation: The underlying closed at $257.13, below the strike price of $260. The call is out of the money.

        Thought: I can answer without using any more tools.
        Answer: The option expired worthless.

        2. Call debit spread simulation/backtesting on NVIDIA
        
        Question: Simulate a call debit spread with the following specifications: expiration date Jan 20th 2023, 3dte, 50 delta for the long call, and 30 delta for the short call (approximately).

        Thought: A call debit spread involves buying a call option at a lower strike price and selling a call option at a higher strike price. A debit spread involves paying a net premium to enter the position. You pay more for the option you buy than you receive for the option you sell.
        I need to use the NVDA tool to find call option contracts with the given dte, expiration date and deltas in order to build a call debit spread.

        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last,
            ABS(o.delta - 0.3) as delta_30_distance, ABS(o.delta - 0.5) as delta_50_distance
            FROM nvda o 
            WHERE o.type = 'C' AND o.expire_date = '2023-01-20' 
            AND o.dte = 3
            AND (delta_30_distance < 0.1 OR delta_50_distance < 0.1);

        Observation: The query returns the following call option contracts:
            quote_date|expire_date|underlying_last|strike|dte|delta|bid|ask|last|delta_30_distance|delta_50_distance
            2023-01-17|2023-01-20|177.02|177.5|3|0.491|3.2|3.25|3.2|0.191|0.00900000000000001
            2023-01-17|2023-01-20|177.02|180|3|0.3746|2.1|2.11|2.09|0.0746|0.1254
            2023-01-17|2023-01-20|177.02|182.5|3|0.26645|1.28|1.32|1.31|0.03355|0.23355

            The long option with the minimum delta_50_distance has a delta of 0.491 and strike price is $177.5. The price of this contract is $3.2 (last traded price).
            The short option with the minimum delta_30_distance has a delta of 0.26645 and strike price is $182.5. The price of this contract is $1.31 (last traded price).
            I need to calculate the net premium paid for this contract by subtracting the short call price from the long call price.
            The net premium paid for this contract is $3.2 - $1.31 = $1.89 (last traded price).
            
        Thought: I need to compute profit/loss by comparing the premium paid for this contract with the the one at expiration date (dte=0). I will use the NVDA tool to find the option prices at expiration date (dte=0).
        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last 
            FROM nvda o 
            WHERE o.type = 'C' AND o.expire_date = '2023-01-20' 
            AND o.dte = 0
            AND ((strike=177.5) OR (strike=182.5))
            LIMIT 2;

        Observation: The query returns the following call option contracts:
            quote_date|expire_date|underlying_last|strike|dte|delta|bid|ask|last
            2023-01-20|2023-01-20|178.38|177.5|0|1|0.81|0.9|0.78
            2023-01-20|2023-01-20|178.38|182.5|0|0.00851|0|0.01|0.01

            The underlying last price was $178.38. The long call with a strike price of $177.5 is in the money. The short call with strike price of $182.5 is out the money.   
            In order to close this trade I need to sell the long ITM call and buy the short OTM call.   
            The long call last price is $0.78 whereas the short call is $0.01.

        Thought: I can answer without using any more tools.
        Answer: The cost to close this trade is the premium paid minus the premium collected, which results in an overall loss of $1.89 - $0.77 = $1.12.

        3. Call credit spread simulation/backtesting on NVDA
        
        Question: Simulate a 3dte call credit spread with expiration date Jan 20th 2023. Pick the best deltas for the trade and calculate profit/loss of the trade at expiration date.

        Thought: A call credit spread involves selling a call at a lower strike price and buying a call at a higher strike price. You collect more for the option you sell than you pay for the option you buy.
        I need to use the NVDA tool to find call option contracts with the given dte and expiration date. I will use a 50 delta for the short call and a 20 delta for the long call.
        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last,
            ABS(o.delta - 0.2) as delta_20_distance, ABS(o.delta - 0.5) as delta_50_distance 
            FROM nvda o 
            WHERE o.type = 'C' AND o.expire_date = '2023-01-20' 
            AND o.dte = 3
            AND (delta_50_distance < 0.1 OR delta_20_distance < 0.1);
            
        Observation: The query returns the following call option contracts:
            quote_date|expire_date|underlying_last|strike|dte|delta|bid|ask|last|delta_20_distance|delta_50_distance
            2023-01-17|2023-01-20|177.02|177.5|3|0.491|3.2|3.25|3.2|0.291|0.00900000000000001
            2023-01-17|2023-01-20|177.02|182.5|3|0.26645|1.28|1.32|1.31|0.06645|0.23355
            2023-01-17|2023-01-20|177.02|185|3|0.18096|0.79|0.8|0.78|0.01904|0.31904
            2023-01-17|2023-01-20|177.02|187.5|3|0.11634|0.45|0.47|0.46|0.08366|0.38366

            For the 50 delta short call, the best option is a contract with the minimum delta_50_distance: a delta of 0.491 and a strike price of $177.5. The premium for this contract is $3.2.
            For the 20 delta long call, the best option is a contract with the minimum delta_20_distance: a delta of 0.18096 and a strike price of $185 with a premium of $0.78.
            Both deltas are within the range of 0.5 and 0.2 respectively.
            The net premium collected for this trade is $3.2 - $0.78 = $2.42.

        Thought: I need to calculate the profit/loss of this trade at expiration. I need to use the NVDA tool to find the prices of these option contracts at expiration date (dte=0) and calculate the cost of closing the trade.
        Action: NVDA
        Action Input:
            SELECT o.quote_date, o.expire_date, o.underlying_last, o.strike, o.dte, o.delta, o.bid, o.ask, o.last 
            FROM nvda o 
            WHERE o.type = 'C' AND o.expire_date = '2023-01-20' 
            AND o.dte = 0
            AND ((strike=177.5) OR (strike=185))
            LIMIT 2;

        Observation: The query returns the following call option contracts:
            quote_date|expire_date|underlying_last|strike|dte|delta|bid|ask|last
            2023-01-20|2023-01-20|178.38|177.5|0|1|0.81|0.9|0.78
            2023-01-20|2023-01-20|178.38|185|0|0.00626|0|0.01|0.01

            The last traded price for these contracts is: $0.78 for the short call and $0.01 for the long call.
        
        Thought: I can answer without using any more tools.
        Answer: The cost of closing this position involves buying the short call and selling the long call: $0.78 - $0.01 = $0.77. The outcome of this trade is the collected premium minus the cost of closing the position at expiration.
        The trade resulted in a net profit of: $2.42 - $0.77 = $2.69.
        
    """

    return context

@st.cache_resource(show_spinner=False)
def create_agent():
    # define LLM
    Settings.llm = NVIDIA(
        model="meta/llama-3.1-405b-instruct",
        temperature=0.5,
        request_timeout=360.0,
    )
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


    sql_database, obj_index = create_db_objectindex()

    # define SQL retriever and query engine
    nl_sql_retriever_spx = NLSQLRetriever(
        sql_database, 
        table_retriever=obj_index.as_retriever(similarity_top_k=1),
        tables=["spx"]
    )

    nl_sql_retriever_nvda = NLSQLRetriever(
        sql_database, 
        table_retriever=obj_index.as_retriever(similarity_top_k=1),
        tables=["nvda"]
    )

    query_engine_spx = RetrieverQueryEngine.from_args(
        nl_sql_retriever_spx,
    )

    query_engine_nvda = RetrieverQueryEngine.from_args(
        nl_sql_retriever_nvda,
    )

    # define tools
    tools = [
        QueryEngineTool.from_defaults(
            query_engine_spx,
            name="SPX", 
            description="Agent that can execute SQL queries to retrieve SPX options contracts.",
        ),
        QueryEngineTool.from_defaults(
            query_engine_nvda,
            name="NVDA", 
            description="Agent that can execute SQL queries to retrieve NVDA options contracts.",
        )
    ]

    # define agent
    context = get_prompt_context()
    agent = ReActAgent.from_tools(
        tools=tools, 
        context=context,
        max_iterations=30,
        verbose=True
    )
    return agent
    

agent = create_agent()

if "agent" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.agent = agent

if prompt := st.chat_input(
    "Ask a question"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Write message history to UI
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_stream = st.session_state.agent.stream_chat(prompt)
            st.write_stream(response_stream.response_gen)
            message = {"role": "assistant", "content": response_stream.response}
            # Add response to message history
            st.session_state.messages.append(message)
