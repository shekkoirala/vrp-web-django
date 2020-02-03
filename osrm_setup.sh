#wget http://download.geofabrik.de/asia/indonesia-latest.osm.pbf
#docker run -t -v "${PWD}:/data" osrm/osrm-backend:v5.22.0 osrm-extract -p /opt/car.lua /data/indonesia-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend:v5.22.0 osrm-partition /data/indonesia-latest.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend:v5.22.0 osrm-partition /data/indonesia-latest.osrm
docker run -t -i -p 9011:5000 -v "${PWD}:/data" osrm/osrm-backend:v5.22.0 osrm-routed --algorithm mld /data/indonesia-latest.osrm


