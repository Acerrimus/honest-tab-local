apt update
apt install -y python3 python3-venv tmux unzip
python3 -m venv ./.venv/obhonesty
source .venv/obhonesty/bin/activate
pip install -r requirements.txt
