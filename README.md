# Datasette API for Green Deal Data Observatory (AWS Ubuntu server installation)

## Datasette Package Installation

Upload the /datasette-install directory to the AWS instance
Install Datasette from the installer directory: python setup.py install
For further info refer to the separate Datasette Readme

## Observatory Deployment

Copy the datasette subdirectory located under /aws-observatory to the server root directory (/home/ubuntu)
Create a symlink for the directory: sudo ln -s /home/ubuntu/datasette /datasette
The symlinked /datasette directory contains the setting files (datasette.service, metadata.json, settings.json) for the Green Deal Observatory API, which will run on port 8000
To enable the service, first set up the DATASETTE_SECRET environment variable in datasette.service (you can use python3 -c 'import secrets; print(secrets.token_hex(32))'), then from the same directory start: sudo bash datasette_service.sh

The python script /datasette/git-append.py will refresh the database from a Github URL
You can set up the repo URL under the # Directory settings section in git-append.py
You will need to generate a Github Deploy Key based on your SSH public key. Then copy your SSH private key to /datasette/contributor (the file in this repo is empty for security reasons). Don't forget to set the chmod to 600

To run the script every hour you can set it up in crontab: "crontab -e", adding the following line:
0 * * * *  python3.8 /datasette/git-append.py 

Nginx and SSL:
You can install Nginx with Certbot/Let's Encrypt on the Ubuntu instance
The recommended Nginx configuration settings are located under the nginx subfolder of /datasette
