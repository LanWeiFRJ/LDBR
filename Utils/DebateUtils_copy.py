import traceback
import time
from os import remove

from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import subprocess
import re
import pandas as pd
import anthropic
from anthropic import DefaultHttpxClient
import httpx

# LLM配置
MODEL_SONNET = "claude-3-5-sonnet-latest"
MODEL_O3 = "o3-mini-2025-01-31"
MODEL_R1 = "deepseek-reasoner"
MODEL_TURBO = "gpt-3.5-turbo"

DEEPSEEK_TOKEN = "Your_Deepseek_Token"
ANTHROPIC_TOKEN = "Your_Anthropic_Token"

TEMPERATURE = 0.7
FREQUENCY_PENALTY = 0.0
PRESENCE_PENALTY = 0.0
INITIAL_SYSTEM_PROMPT = "You are a senior bug report expert."
INITIAL_USER_PROMPT = "Please generate the executable test case using Java to trigger the bug in the report."


def infer_with_llm(prompt, model, max_retries=5, initial_delay=1.0, backoff_factor=2.0):
    retry_count = 1
    current_delay = initial_delay

    # 初始化OpenAI API
    if model == "sonnet" :
        client = anthropic.Anthropic(
            api_key=ANTHROPIC_TOKEN,
            http_client=DefaultHttpxClient(
                proxy="http://127.0.0.1:7897",
                transport=httpx.HTTPTransport(local_address="0.0.0.0")
            )
        )

        while retry_count <= max_retries:
            try:
                response = client.messages.create(
                    model=MODEL_SONNET,
                    max_tokens=2000,
                    system=INITIAL_SYSTEM_PROMPT + INITIAL_USER_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )

                return response.content[0].text.strip()

            except:
                if retry_count < max_retries:
                    print("Fail " + str(retry_count) + " times")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    retry_count += 1
                else:
                    raise Exception(f"Max Retries")

        raise Exception("Unexpected Fault. Over max retries.")

    elif model == "r1":
        client = OpenAI(api_key=DEEPSEEK_TOKEN, base_url="https://api.deepseek.com")

        while retry_count <= max_retries:
            try:
                response = client.chat.completions.create(
                    model=MODEL_R1,
                    messages=[
                        {"role": "system", "content": INITIAL_SYSTEM_PROMPT + INITIAL_USER_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )

                return response.choices[0].message.content.strip()

            except:
                if retry_count < max_retries:
                    print("Fail " + str(retry_count) + " times")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    retry_count += 1
                else:
                    raise Exception(f"Max Retries")

        raise Exception("Unexpected Fault. Over max retries.")

    elif model == "turbo" or model =="o3":
        client = OpenAI()
        if model == "o3":
            model_gpt = MODEL_O3
        else:
            model_gpt = MODEL_TURBO
        
        while retry_count <= max_retries:
            try:
                response = client.chat.completions.create(
                    model=model_gpt,
                    messages=[
                        {"role": "system", "content": INITIAL_SYSTEM_PROMPT},
                        {"role": "user", "content": INITIAL_USER_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )

                return response.choices[0].message.content.strip()

            except:
                if retry_count < max_retries:
                    print("Fail " + str(retry_count) + " times")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    retry_count += 1
                else:
                    raise Exception(f"Max Retries")

        raise Exception("Unexpected Fault. Over max retries.")

    elif model == "o3" :
        client = OpenAI()
        model = MODEL_O3

        while retry_count <= max_retries:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": INITIAL_SYSTEM_PROMPT},
                        {"role": "user", "content": INITIAL_USER_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )

                return response.choices[0].message.content.strip()

            except:
                if retry_count < max_retries:
                    print("Fail " + str(retry_count) + " times")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    retry_count += 1
                else:
                    raise Exception(f"Max Retries")

        raise Exception("Unexpected Fault. Over max retries.")


def fetch_bug_report(url, max_retries=5, initial_delay=1, backoff_factor=2):
    retries = 0
    current_delay = initial_delay

    while retries < max_retries:
        try:
            response = requests.get(url, timeout=(5, 15))

            response.raise_for_status()

            return response.text

        except (requests.exceptions.RequestException,
                ValueError) as e:
            print(f"Request Failure ({type(e).__name__}): {str(e)}")
            print(f"{retries + 1}/{max_retries} retries，retry after {current_delay} seconds...")

            retries += 1
            if retries < max_retries:
                time.sleep(current_delay)
                current_delay *= backoff_factor
    raise requests.exceptions.RetryError(
        f"Fail, Max Retries."
    )


def generate_prompt(html_content, state_code, code=None):
    """
    Generate a prompt for LLM
    :param html_content: Html content got from url
    :param code: code generated by another agent
    :param state_code: 1 for regular bug reproduce, 2 for debating
    :return: prompt
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    bug_report_text = soup.get_text()
    if state_code == 1:
        prompt = f"""
        Please generate a JUnit style Java test case based on the provided bug report, it should satisfy the requests below:

           - Use Java to reproduce the bug.
           - If there is not any code in the original bug report, generate the code according to the description.

        An example of bug report and the corresponding test case is given below:

            Bug Report:
                Parsing a HTML snippet causes the leading text to be moved to back

                Code:

                String html = "foo <b>bar</b> baz";
                String text = Jsoup.parse(html).text();
                System.out.println(text);

                Result:

                bar baz foo

                Excepted:

                foo bar baz

            Test Case:
                import org.jsoup.Jsoup;
                import static org.junit.Assert.*;
                import org.junit.Test;

                public class HtmlParserBugTest {{
                    @Test
                    public void testTextOrder() {{
                        String html = "foo <b>bar</b> baz";
                        String actual = Jsoup.parse(html).text();
                        assertEquals("foo bar baz", actual);
                    }}
                }}

        Ensure the scripts is free of any Markdown, descriptions, or comments. The output should be plain Java code.

        Bug Report:
        {bug_report_text}
        """
    else:
        prompt = f"""
        1.Assuming that you are a senior bug-reproducing professor and you are debating against another bug-reproducing professor, according to the bug report, analyze the reproduction code I give you below, and list the flaws in your opponent's argument.

            Bug Report:

            {bug_report_text}

            Reproduction Code:

            {code}

        2.Your answer should satisfy the requests below:

            - Thinking step by step, critique your opponent's argument and show your thinking process.
            - Generate your bug-reproducing code, and it should be in **JUnit style**.
            - When generating the code, pay attention to the source compatibility version, which is set to 6 in the testing environment.
            - Wrap the reproduced code you generate with markdown-style triple backticks (```), which is **extremely important**.

        3.Here I will give you an example of bug reproduction:

            Bug Report:

            Parsing a HTML snippet causes the leading text to be moved to back

                    BalusC opened on May 28, 2010

                    Code:

                        String html = "foo <b>bar</b> baz";
                        String text = Jsoup.parse(html).text();
                        System.out.println(text);

                    Result:

                        bar baz foo

                    Excepted:

                        foo bar baz

            Knowledge in bug reproduction:

            - Environment consistency: Choose correct repository version according to the time of the report.
            - Data and Input reproduction: Use the same data/input as the report did.

            Reproduction Code:

            ```
            import org.jsoup.Jsoup;
            import static org.junit.Assert.*;
            import org.junit.Test;

            public class HtmlParserBugTest {{
                @Test
                public void testTextOrder() {{
                    String html = "foo <b>bar</b> baz";
                    String actual = Jsoup.parse(html).text();
                    assertEquals("foo bar baz", actual);
                }}
            }}
            ```
                """
    return prompt


def execute_script(file_path):
    subprocess.run(["chmod", "+x", file_path])
    result = subprocess.run(["sh", file_path], capture_output=True, text=True)
    return result.stdout, result.stderr


def remove_backticks(response):
    if response.startswith('```'):
        response = response[3:]
    if response.startswith('java'):
        response = response[4:]
    if response.endswith('```'):
        response = response[:-3]
    return response

def iterator(url_list, i, model1, model2):
    model_start = model1
    model_counter = model2

    cur_url = url_list[i - 1]
    print(cur_url)
    html_content = fetch_bug_report(cur_url)
    print("fetch done")
    prompt = generate_prompt(html_content, state_code=1)
    print("prompt generation done")
    response = infer_with_llm(prompt, model=model_start)
    print("response generation done")
    code = remove_backticks(response)

    pattern = r'```\s*(?:java\s*)?\n(.*?)\s*```'

    # Debate Round 1
    prompt1 = generate_prompt(html_content, 2, code)
    response1 = infer_with_llm(prompt1, model=model_counter)
    pre_code1 = re.search(pattern, response1, flags=re.DOTALL).group(0)
    code1 = remove_backticks(pre_code1)

    _prompt1 = generate_prompt(html_content, 2, code1)
    _response1 = infer_with_llm(_prompt1, model=model_start)
    _pre_code1 = re.search(pattern, _response1, flags=re.DOTALL).group(0)
    _code1 = remove_backticks(_pre_code1)
    print("Round 1 done.")

    # Debate Round 2
    prompt2 = generate_prompt(html_content, 2, _code1)
    response2 = infer_with_llm(prompt2, model=model_counter)
    pre_code2 = re.search(pattern, response2, flags=re.DOTALL).group(0)
    code2 = remove_backticks(pre_code2)

    _prompt2 = generate_prompt(html_content, 2, code2)
    _response2 = infer_with_llm(_prompt2, model=model_start)
    _pre_code2 = re.search(pattern, _response2, flags=re.DOTALL).group(0)
    _code2 = remove_backticks(_pre_code2)
    print("Round 2 done.")

    # Debate Round 3
    prompt3 = generate_prompt(html_content, 2, _code2)
    response3 = infer_with_llm(prompt3, model=model_counter)
    pre_code3 = re.search(pattern, response3, flags=re.DOTALL).group(0)
    code3 = remove_backticks(pre_code3)

    _prompt3 = generate_prompt(html_content, 2, code3)
    _response3 = infer_with_llm(_prompt3, model=model_start)
    _pre_code3 = re.search(pattern, _response3, flags=re.DOTALL).group(0)
    _code3 = remove_backticks(_pre_code3)
    print("Round 3 done.")

    _code3 += '\nEOF_JAVA_CODE'
    _response3 += '\nEOF_RESPONSE'

    return _code3, response1, response2, response3, _response1, _response2, _response3