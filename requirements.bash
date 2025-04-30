sudo apt update
sudo apt install -y python3 python3-pip unzip
mkdir -p .venvs
python -m venv .venvs/default-env
source .venvs/default-env/bin/activate
pip install -r requirements.txt