# sudo docker pull mysql
sudo docker rm -f mysql
sudo docker run --name=mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=12qwaszx -v /home/vishwa/mysql:/var/lib/mysql -d mysql
sleep 5
sudo mysql --host=0.0.0.0 --port=3306 -uroot -p12qwaszx -e "CREATE DATABASE user_auth_db;"
