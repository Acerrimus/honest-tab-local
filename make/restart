timedatectl set-timezone Europe/Madrid
timedatectl set-ntp on
./make/build.bash
tmux kill-server
fuser -k -TERM 8765/tcp
git checkout -f main
git pull
tmux new-session -d -s obhonesty './make/run_prod.bash'
