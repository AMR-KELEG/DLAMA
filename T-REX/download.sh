# Download the data
wget -c "https://figshare.com/ndownloader/files/8760241"
mv 8760241 full.zip

mkdir json-files/

cd json-files
unzip ../full.zip

cd ../
mkdir parsed-data
python parse_trex.py
