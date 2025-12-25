

_default:
    @just -l

# build docs for all tags
build-all:
    ./scripts/build.sh all

# remove all build artifacts
clean:
    ./scripts/build.sh clean
