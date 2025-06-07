#!/bin/bash

#Default prefix
prefix="Cli"

while getopts ":p:" opt; do
	case $opt in
		p)
			prefix="$OPTARG"
			;;
		\?)
			echo "No such arg as -$OPTARG" >&2
			exit 1
			;;
		:)
			echo "option -$OPTARG needs a parameter" >&2
			exit 1
			;;
	esac
done

shift $((OPTIND-1))

for i in {1..5}; do
    # run python script and asve the results
    python Basic_${prefix}.py -m sonnet> "Results_Basic/${prefix}/output_${i}.txt"
    
    # 运行 results_claculate_basic.py 并追加到同一文件
    python3 results_calculate_basic.py -p {prefix} > Results_Basic/${prefix}/combined_results_${i}.log
done