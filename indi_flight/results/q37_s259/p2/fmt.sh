cd /tmp/indi_fwbranch_s251; n=0; bad=0
while read f; do n=$((n+1)); out=$(Tools/astyle/fix_code_style.sh --dry-run --formatted "$f" 2>&1); [ -n "$out" ] && { bad=$((bad+1)); echo "$out" | head -5; }; done < /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/q37_s259/p2/changed_cpp_files.txt
echo "checked=$n reported=$bad"
