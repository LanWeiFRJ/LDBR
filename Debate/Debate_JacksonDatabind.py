import Utils.DebateUtils as du
import sys

if __name__ == "__main__":
    path = r"active-bugs-JacksonDatabind.csv"
    data = du.pd.read_csv(path, encoding='gbk')
    url_list = data['report.url'].values.tolist()
    index_list = data['bug.id'].values.tolist()
    model1 = "sonnet"
    model2 = "o3"

    # m1, m2 = "sonnet", "o3", "r1", "nano"
    if "-m" in sys.argv:
        p_index1 = sys.argv.index("-m") + 1
        model1 = sys.argv[p_index1]
    if "-n" in sys.argv:
        p_index2 = sys.argv.index("-n") + 1
        model2 = sys.argv[p_index2]

    # i为bug序号，作为索引来检索bug的url
    for i in index_list:
        try:
            _code3, response1, response2, response3, _response1, _response2, _response3 = du.iterator(url_list, i, model1, model2, "JacksonDatabind")
            # 用正则表达式匹配“public class ***”
            class_name = du.re.search(r"(?<=\bpublic\sclass\s)[A-Z][a-zA-Z0-9_]*", _code3, du.re.DOTALL).group(0)

            configure_script = f"""
            rm -rf /home/lanweifrj/Test_Total/JacksonDatabind_buggy/JacksonDatabind_{i}_buggy
            
            defects4j checkout -p JacksonDatabind -v {i}b -w /home/lanweifrj/Test_Total/JacksonDatabind_buggy/JacksonDatabind_{i}_buggy
            
            cd /home/lanweifrj/Test_Total/JacksonDatabind_buggy/JacksonDatabind_{i}_buggy
            
            mkdir responses
            
            cd responses
            
            cat << 'EOF_RESPONSE' > response
            response1_model1: 
            {response1}
            --------------------
            response1_model2:
            {_response1}
            --------------------
            response2_model1:
            {response2}
            --------------------
            response2_model2:
            {_response2}
            --------------------
            response3_model1:
            {response3}
            --------------------
            response3_model2:
            {_response3}

            cd /home/lanweifrj/Test_Total/JacksonDatabind_buggy/JacksonDatabind_{i}_buggy/src/test/java/com/fasterxml/jackson/databind

            CUR="$PWD"

            touch {class_name}.java

            cat << EOF_JAVA_CODE > {class_name}.java
            package com.fasterxml.jackson.$(basename "$CUR");
            {_code3}

            cd /home/lanweifrj/Test_Total/JacksonDatabind_buggy/JacksonDatabind_{i}_buggy

            defects4j compile > /home/lanweifrj/Test_Total/JacksonDatabind_buggy/results/debate/result_{i}.txt

            defects4j test >> /home/lanweifrj/Test_Total/JacksonDatabind_buggy/results/debate/result_{i}.txt
            """

            script_path = f"/home/lanweifrj/Test_Total/JacksonDatabind_buggy/scripts/configure_script_{i}.sh"
            with open(script_path, "w") as f:
                f.write(configure_script)
            result_cor, result_err = du.execute_script(script_path)
            if result_cor:
                print("No." + str(i) + " correct.\n")
            if result_err:
                print("No." + str(i) + " error.\n")
                print(result_err)
                with open(f"/home/lanweifrj/Test_Total/JacksonDatabind_buggy/errors/debate/error_log_{i}.txt", "w") as f:
                    f.write(result_err)

            print("buggy done.")

            # Fixed Version

            configure_script = f"""
            rm -rf /home/lanweifrj/Test_Total/JacksonDatabind_fixed/JacksonDatabind_{i}_fixed
            
            defects4j checkout -p JacksonDatabind -v {i}f -w /home/lanweifrj/Test_Total/JacksonDatabind_fixed/JacksonDatabind_{i}_fixed

            cd /home/lanweifrj/Test_Total/JacksonDatabind_fixed/JacksonDatabind_{i}_fixed/src/test/java/com/fasterxml/jackson/databind

            CUR="$PWD"

            touch {class_name}.java

            cat << EOF_JAVA_CODE > {class_name}.java
            package com.fasterxml.jackson.$(basename "$CUR");
            {_code3}

            cd /home/lanweifrj/Test_Total/JacksonDatabind_fixed/JacksonDatabind_{i}_fixed

            defects4j compile > /home/lanweifrj/Test_Total/JacksonDatabind_fixed/results/debate/result_{i}.txt

            defects4j test >> /home/lanweifrj/Test_Total/JacksonDatabind_fixed/results/debate/result_{i}.txt
            """

            script_path = f"/home/lanweifrj/Test_Total/JacksonDatabind_fixed/scripts/configure_script_{i}.sh"
            with open(script_path, "w") as f:
                f.write(configure_script)
            result_cor, result_err = du.execute_script(script_path)
            if result_cor:
                print("No." + str(i) + " correct.\n")
            if result_err:
                print("No." + str(i) + " error.\n")
                print(result_err)
                with open(f"/home/lanweifrj/Test_Total/JacksonDatabind_fixed/errors/debate/error_log_{i}.txt",
                          "w") as f:
                    f.write(result_err)

            print("fixed done.")

        except:
            with open(f"/home/lanweifrj/Test_Total/JacksonDatabind_buggy/errors/debate/fatal_log_{i}.txt", "w") as f:
                f.write(du.traceback.format_exc())
            pass
