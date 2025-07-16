
# Development Environment for UI #

## Run ##
```shell
  # with Parcel CLI
  npx parcel-bundler index.html --open
  
  # with package.json scripts using Parcel
  npm run build
  npm run start
```

# Deployment #
```shell
  # install as static server
  npm install -g serve
  # start static server with PM2
  pm2 start serve --name "feeyu-ui" -- -s /path/to/ui/dist -l 3000
  # save PM2 process list
  pm2 save
```
