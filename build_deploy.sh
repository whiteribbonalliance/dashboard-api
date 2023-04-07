#az login
#az acr login --name regprotocolsfds
export COMMIT_ID=`git show -s --format=%ci_%h | sed s/[^_a-z0-9]//g | sed s/0[012]00_/_/g`
docker build -t wwwapi --build-arg COMMIT_ID=$COMMIT_ID .
docker tag wwwapi gcr.io/deft-stratum-290216/wwwapi:$COMMIT_ID
docker push gcr.io/deft-stratum-290216/wwwapi:$COMMIT_ID
echo "The container version is $COMMIT_ID"