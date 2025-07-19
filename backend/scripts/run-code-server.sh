docker run -d \
  --name=code-server-1 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e DEFAULT_WORKSPACE=/config/workspace \
  -p 8442:8443 \
  -v $PWD/config:/config \
  --hostname=cxl-dev \
  --restart unless-stopped \
  cxl.io/dev/code-server:latest

  # -e PASSWORD=password `#optional` \
  # -e HASHED_PASSWORD= `#optional` \
  # -e SUDO_PASSWORD=password `#optional` \
  # -e SUDO_PASSWORD_HASH= `#optional` \
  # -e PROXY_DOMAIN=code-server.my.domain `#optional` \
