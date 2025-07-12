import Utils.BasicUtils as bu
import sys

if __name__ == "__main__":
    path = r"active-bugs-Cli.csv"
    data = bu.pd.read_csv(path, encoding='gbk')
    url_list = data['report.url'].values.tolist()
    index_list = data['bug.id'].values.tolist()
    model = "sonnet"

    # m = "sonnet", "o3", "r1", "turbo"
    if "-m" in sys.argv:
        p_index = sys.argv.index("-m") + 1
        model = sys.argv[p_index]

    # i为bug序号，作为索引来检索bug的url
    for i in index_list:
        try:
            code = bu.iterator(url_list, i, model, "Cli")
            # 用正则表达式匹配“public class ***”
            class_name = bu.re.search(r"(?<=\bpublic\sclass\s)[A-Z][a-zA-Z0-9_]*", code, bu.re.DOTALL).group(0)

            # Buggy Version

            if i < 30 :
                configure_script = f"""
                rm -rf /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy
                
                defects4j checkout -p Cli -v {i}b -w /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy
    
                cd /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy/src/test/org/apache/commons/cli*
                
                CUR="$PWD"
    
                touch {class_name}.java
    
                cat << EOF_JAVA_CODE > {class_name}.java
                package org.apache.commons.$(basename "$CUR");
                {code}
    
                cd /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy
    
                defects4j compile > /home/lanweifrj/Test_Total/Cli_buggy/results/basic/result_{i}.txt
    
                defects4j test >> /home/lanweifrj/Test_Total/Cli_buggy/results/basic/result_{i}.txt
                """
            else :
                configure_script = f"""
                rm -rf /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy
                
                defects4j checkout -p Cli -v {i}b -w /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy

                cd /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy/src/test/java/org/apache/commons/cli*
                
                CUR="$PWD"
                
                touch {class_name}.java

                cat << EOF_JAVA_CODE > {class_name}.java
                package org.apache.commons.$(basename "$CUR");
                {code}

                cd /home/lanweifrj/Test_Total/Cli_buggy/Cli_{i}_buggy

                defects4j compile > /home/lanweifrj/Test_Total/Cli_buggy/results/basic/result_{i}.txt

                defects4j test >> /home/lanweifrj/Test_Total/Cli_buggy/results/basic/result_{i}.txt
                """

            script_path = f"/home/lanweifrj/Test_Total/Cli_buggy/scripts/configure_script_{i}.sh"
            with open(script_path, "w") as f:
                f.write(configure_script)
            result_cor, result_err = bu.execute_script(script_path)
            if result_cor:
                print("No." + str(i) + " correct.\n")
            if result_err:
                print("No." + str(i) + " error.\n")
                print(result_err)
                with open(f"/home/lanweifrj/Test_Total/Cli_buggy/errors/basic/error_log_{i}.txt", "w") as f:
                    f.write(result_err)

            print("buggy done.")

            # Fixed Version
            if i < 30:
                configure_script = f"""
                rm -rf /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed
                
                defects4j checkout -p Cli -v {i}f -w /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed

                cd /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed/src/test/org/apache/commons/cli*
                
                CUR="$PWD"

                touch {class_name}.java

                cat << EOF_JAVA_CODE > {class_name}.java
                package org.apache.commons.$(basename "$CUR");
                {code}

                cd /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed

                defects4j compile > /home/lanweifrj/Test_Total/Cli_fixed/results/basic/result_{i}.txt

                defects4j test >> /home/lanweifrj/Test_Total/Cli_fixed/results/basic/result_{i}.txt
                """
            else:
                configure_script = f"""
                rm -rf /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed
                
                defects4j checkout -p Cli -v {i}f -w /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed

                cd /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed/src/test/java/org/apache/commons/cli*
                
                CUR="$PWD"

                touch {class_name}.java

                cat << EOF_JAVA_CODE > {class_name}.java
                package org.apache.commons.$(basename "$CUR");
                {code}

                cd /home/lanweifrj/Test_Total/Cli_fixed/Cli_{i}_fixed

                defects4j compile > /home/lanweifrj/Test_Total/Cli_fixed/results/basic/result_{i}.txt

                defects4j test >> /home/lanweifrj/Test_Total/Cli_fixed/results/basic/result_{i}.txt
                """

            script_path = f"/home/lanweifrj/Test_Total/Cli_fixed/scripts/configure_script_{i}.sh"
            with open(script_path, "w") as f:
                f.write(configure_script)
            result_cor, result_err = bu.execute_script(script_path)
            if result_cor:
                print("No." + str(i) + " correct.\n")
            if result_err:
                print("No." + str(i) + " error.\n")
                print(result_err)
                with open(f"/home/lanweifrj/Test_Total/Cli_fixed/errors/basic/error_log_{i}.txt", "w") as f:
                    f.write(result_err)

            print("fixed done.")

        except:
            with open(f"/home/lanweifrj/Test_Total/Cli_buggy/errors/basic/fatal_log_{i}.txt", "w") as f:
                f.write(bu.traceback.format_exc())
            pass
