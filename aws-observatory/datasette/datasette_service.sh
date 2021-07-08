sudo cp datasette.service /etc/systemd/system/datasette.service
sudo systemctl daemon-reload
sudo systemctl stop datasette.service
sudo systemctl enable datasette.service
sudo systemctl start datasette.service
sudo systemctl status datasette.service