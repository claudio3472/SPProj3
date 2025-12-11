set -e

SERVER_FILE="server.enc"
RESULT="result.enc"
ENCR_DATA="data.enc"

if [ $# -ne 2 ]; then
	echo "Usage $0 <scheme> <data_to_work_with>"	
	exit 1
fi

printf "Encrypting data"
time python DataHolder.py e $1 $2 $SERVER_FILE $ENCR_DATA

printf "\nAnalizing data"
time python DataAnalyzer.py $ENCR_DATA $RESULT

printf "\nShowing Results\n"
time python DataHolder.py d $SERVER_FILE $RESULT

