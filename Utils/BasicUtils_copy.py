import traceback
from email.policy import default

from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import subprocess
import re
import pandas as pd
import time
import httpx
import anthropic
from anthropic import DefaultHttpxClient

# LLM配置
MODEL_SONNET = "claude-3-5-sonnet-latest"
MODEL_O3 = "o3-mini-2025-01-31"
MODEL_R1 = "deepseek-reasoner"
MODEL_TURBO = "gpt-3.5-turbo"

DEEPSEEK_TOKEN = "your_key"
ANTHROPIC_TOKEN = "your_key"

TEMPERATURE = 0.7
FREQUENCY_PENALTY = 0.0
PRESENCE_PENALTY = 0.0
INITIAL_SYSTEM_PROMPT = "You are a senior bug report expert."
INITIAL_USER_PROMPT = "Please generate the executable test case using Java to trigger the bug (only trigger but not solve the bug) in the report."

def infer_with_llm(prompt, model, max_retries=5, initial_delay=1.0, backoff_factor=2.0):

    retry_count = 1
    current_delay = initial_delay

    if model == "sonnet":
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
                                    "type" : "text",
                                    "text" : prompt
                                }
                            ]
                        }
                    ]
                )

                return response.content[0].text.strip()

            except :
                if retry_count < max_retries:
                    print("Fail " + str(retry_count) + " times")

                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    retry_count += 1
                else:
                    raise Exception(f"Max Retries")

        raise Exception("Unexpected Fault. Over max retries.")

    elif model == "o3" or model == "turbo":
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

def generate_prompt(html_content, repo):

    class_1 = "aui-item issue-main-column"
    class_2 = "Box-sc-g0xbh4-0 dxnHPp"

    repo_to_html_class = {
        "Cli": class_1,
        "Codec": class_1,
        "Collections": class_1,
        "Compress": class_1,
        "Csv": class_1,
        "JxPath": class_1,
        "Lang": class_1,
        "Math": class_1,
        "Gson": class_2,
        "JacksonXml": class_2,
        "JacksonCore": class_2,
        "JacksonDatabind": class_2,
        "Jsoup": class_2,
        "Time": class_2
    }

    soup = BeautifulSoup(html_content, 'html.parser')
    bug_report_text = soup.find('div', class_=repo_to_html_class[repo]).get_text(strip=True, separator=' ')
    prompt = f"""
    Bug Report:

        {bug_report_text}
        
    Please generate a JUnit style Java test case based on the provided bug report, it should satisfy the requests below:

        - Think step by step.
        - Generate your bug-reproducing code, and it should be in **JUnit 3 style**.
        - When generating the code, pay attention to the source compatibility version, which is set to 6 in the testing environment.
        - Before you give me the code, recall related knowledge, such as environment consistency, to help your generation.
        - Wrap the reproduced code you generate with markdown-style triple backticks (```), which is **extremely important**.

    Here I will give you an example of bug reproduction:

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

def remove_backticks(response):
    if response.startswith('```'):
        response = response[3:]
    if response.startswith('java'):
        response = response[4:]
    if response.endswith('```'):
        response = response[:-3]
    return response

def execute_script(file_path):
    subprocess.run(["chmod", "+x", file_path])
    result = subprocess.run(["sh", file_path], capture_output=True, text=True)
    return result.stdout, result.stderr

def iterator(url_list, i, model, repo):
    cur_url = url_list[i - 1]
    print(cur_url)
    html_content = fetch_bug_report(cur_url)
    print("fetch done")
    prompt = generate_prompt(html_content, repo)
    print("prompt generation done")
    response = infer_with_llm(prompt, model)
    print("response generation done")

    pattern = r'```\s*(?:java\s*)?\n(.*?)\s*```'
    pre_code = re.search(pattern, response, flags=re.DOTALL).group(0)

    code = remove_backticks(pre_code)
    code += '\nEOF_JAVA_CODE'

    return code
