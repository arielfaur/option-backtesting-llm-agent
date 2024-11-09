# ReAct Agent with Financial Knowledge for Option Backtesting
*NVIDIA and LlamaIndex Developer Contest 2024 Submission Project*

## Environment
- Jupyter notebook
- LlamaIndex framework
- Nvidia NIM inference microservices (model: Llama 3.1 405B)
- Local SQLite database with Nvidia and SPX index option historical data

## Overview
This is a Python notebook that implements a ReActAgent to simulate financial trades and backtest Nvidia and SPX options strategies. The agent is trained by means of a fine-tuned prompt with few shot examples that describe in detail the steps the agent needs to perform in order to backtest specific strategies. This ensures the agent stays on topic and prevents hallucinations.

The agent has access to an external tool - an SQL agent capable of translating natural language into SQL queries (text-to-SQL). This is a SQLite database with Nvidia and SPX index historical options data for the year 2023. As of now, the agent is capable of backtesting option strategies at a given date and data is limited to the year 2023.

## Motivation
Being myself a trader, I wanted to find a different approach to backtesting options strategies that does not involve coding, as opposed to the majority of backtesting platforms. I thought using an LLM agent would be a disruptive use case scenario, given that LLMs are not specialized for this purpose. The challenge seemed to be a good opportunity for me to gain a better understanding of agents and prompt engineering.

## Results
The agent is able to perform a backtest of commom strategies -such as put or credit spreads- at a given date. Performing a backtest over a date range hasn't been tested yet - although I suppose this will be really time and resource consuming - considering the response time.

### Financial strategies tested
As of now, the following financial strategies have been tested:

- Call debit spreads
- Call credit spreads
- Put credit spreads


### Challenges
These were the challenges faced in order to have the model perform the task successfully, which required extensive research and a trial-and-error approach:

*Model*

Several open source models were tested for this use case scenario. However, two of them showed the best results for function/tool calling agents (more specifically the text-to-SQL task):
- Mistral-NeMo 12B
- Meta Llama 3.1 405B

*Prompt engineering*

The prompt has been highly tuned with few shot examples that describe in detail the steps the agent needs to perform to backtest specific strategies. This is the most time-consuming but required in order to minimize hallucinations.


## Current Issues
1. Llama limited support for function/tool calling: the model seems to fail to recognize the external tool call during the first few iterations and responds with the error below. Then it finally corrects itself and uses the tool as expected. This is likely due to the model not being trained on this specific use case scenario.

   
        Observation: Error: Could not parse output. Please follow the thought-action-input format. Try again.
   

    https://github.com/run-llama/llama_index/issues/12699


2. Reasoning loops: sometimes the model may get stuck in a "reasoning" loop, even though it has the necessary information to synthesize a response.

3. Model performance: the model is slower at producing a final response, compared to the speed performance of an algorithmic approach. 


4. Hallucination: even though the prompt has been highly customized/tuned to avoid hallucination, the model may still produce a response that is not precise, especially for strategies that haven't been described in the prompt.


## Future Work
- Prompt engineering: extend the prompt to support more trading strategies.
- Backtesting: extend the agent to support backtesting over a date range.

## Data sources
[optionsDX](https://www.optionsdx.com)
- free historical end-of-day options data in CSV format
- transformed and imported into a SQLite database

## References
- [ReAct Prompting](https://www.promptingguide.ai/techniques/react)
- [The Few Shot Prompting Guide](https://www.prompthub.us/blog/the-few-shot-prompting-guide#why-use-few-shot-prompting)
- [Text-to-SQL Guide](https://docs.llamaindex.ai/en/stable/examples/index_structs/struct_indices/SQLIndexDemo/#part-3-text-to-sql-retriever)