cd /tmp/indi_fwbranch_s248; n=0; bad=0
while read f; do n=$((n+1)); out=$(Tools/astyle/fix_code_style.sh --dry-run --formatted "$f" 2>&1); [ -n "$out" ] && { bad=$((bad+1)); echo "$out" | head -5; }; done < /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g7_s248/changed_cpp_files.txt
echo "checked=$n reported=$bad"
