# Example site for hugo-theme-gallery

## Installation

Review your hugo version compared to the one required by the theme `hugo.toml`

```sh
#cd exampleSite

# Install Hugo module
hugo mod get

# Pull example images from Unsplash
./pull-images.sh
```

If you dont have the right version: you can use the `Dockerfile` to build a container with the right version of Hugo and develop locally via `docker-compose-dev.yml`:

```sh
make build
make up
```

When you are done with the changes:

```sh
#docker exec -it hugo hugo version
docker exec -it -w /hugo-theme-gallery/exampleSite hugo hugo
```

Then, the `public` folder will be available at `./hugo-theme-gallery/exampleSite/public`

And 