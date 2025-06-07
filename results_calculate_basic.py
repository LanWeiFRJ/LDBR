import os
import sys
import re
import subprocess

if __name__ == "__main__":

    hash_table = {}
    param_value = ''
    total = 0

    hash_table["Cli"] = 39
    hash_table["Closure"] = 174
    hash_table["Codec"] = 18
    hash_table["Collections"] = 28
    hash_table["Compress"] = 47
    hash_table["Csv"] = 16
    hash_table["Gson"] = 18
    hash_table["JacksonCore"] = 26
    hash_table["JacksonDatabind"] = 110
    hash_table["JacksonXml"] = 6
    hash_table["Jsoup"] = 93
    hash_table["JxPath"] = 22
    hash_table["Lang"] = 61
    hash_table["Math"] = 106
    hash_table["Time"] = 26

    if "-p" in sys.argv:
        p_index = sys.argv.index("-p") + 1
        param_value = sys.argv[p_index]
        total = hash_table[param_value]

    i = 1
    correct_buggy = 0
    correct_fixed = 0
    correct_total = 0
    while i <= total :
        flag_buggy = False
        flag_fixed = False

        index_name_buggy = f"""/home/lanweifrj/Test_Total/{param_value}_buggy/results/basic/result_{i}.txt"""
        index_name_fixed = f"""/home/lanweifrj/Test_Total/{param_value}_fixed/results/basic/result_{i}.txt"""

        if not os.path.exists(index_name_buggy) or not os.path.exists(index_name_fixed):
            print(f"""No. {i} do not exist.""")
            i += 1
            continue

        try :
            with open(index_name_fixed, "r", encoding="utf-8") as f:
                text = f.read().strip()

            # Fixed Version
            match = re.search(r"Failing tests:\s*(\d+)", text)
            if match:
                num_fixed_str = match.group(1)
                num_fixed = int(num_fixed_str)
                if num_fixed == 0:
                    correct_fixed += 1
                    print(f"""No. {i} fixed version success.""")
                    flag_fixed = True
                else:
                    print(f"""No, {i} fixed version failed.""")
            else:
                print(f"""No, {i} fixed version failed.""")

            # Buggy Version
            command = ["defects4j", "info", "-p", param_value, "-b", str(i)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            matches = re.findall(f"-->", output)
            original = len(matches)

            with open(index_name_buggy, "r", encoding="utf-8") as f1:
                _text = f1.read().strip()

            _match = re.search(r"Failing tests:\s*(\d+)", _text)
            if _match:
                num_buggy_str = _match.group(1)
                num_buggy = int(num_buggy_str)
                if num_buggy - original == 1:
                    correct_buggy += 1
                    print(f"""No. {i} buggy version success.""")
                    flag_buggy = True
                else:
                    print(f"""No. {i} buggy version failed.""")
            else:
                print(f"""No. {i} buggy version failed.""")

            if flag_buggy and flag_fixed:
                correct_total += 1

            i += 1
        except Exception as e:
            print(f"""No. {i} fatal.""")
            print(e.__traceback__)

    print("buggy:" + str(correct_buggy))
    print("fixed:" + str(correct_fixed))
    print("both:" + str(correct_total))
