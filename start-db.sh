docker run \
	-v "$(pwd)/reproducible.sql:/docker-entrypoint-initdb.d/data.sql" \
	-v "$(pwd)/data/:/var/lib/postgresql/data" \
	-p "127.0.0.1:5000:5432" \
       	-e POSTGRES_USER=rb \
	-e POSTGRES_DB=rbdb \
	-e POSTGRES_PASSWORD=foo \
	--rm postgres:alpine

