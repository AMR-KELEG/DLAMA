FILES=$(ls parsed-data/)
for FILE in $FILES
do
    echo $FILE
    cat parsed-data/$FILE | sort | uniq > unique-dump/$FILE
done
