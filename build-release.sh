#! /bin/sh
set -e

for arg; do
    case "$arg" in
    --version=*)
        VERSION=${arg#*=}
        ;;
    --help)
        echo "Usage: --version=<ver>"
        exit 0
        ;;
    -*)
        echo "Unknown arg $arg" >&2
        exit 1
        ;;
    *)
        break
        ;;
    esac
done

RELEASEDIR="$(pwd)/release"
echo "Release Directory: $RELEASEDIR"
echo "Version: $VERSION"

if [ "$VERSION" = "" ]; then
    echo "Error: No version specified!"
    exit 1
fi

mkdir -p "$RELEASEDIR"

echo "Creating Zip File"
[ -f "$RELEASEDIR/clnrest-$VERSION.zip" ] && rm "$RELEASEDIR/clnrest-$VERSION.zip"
mkdir "$RELEASEDIR/clnrest-$VERSION"
rsync -av --include='/utilities/' --include='/cln_rest.py' --include='/clnrest.py' --include="/requirements.txt" --exclude="*" "./" "$RELEASEDIR/clnrest-$VERSION"
cd "$RELEASEDIR" && zip -r -X "clnrest-$VERSION.zip" .
rm -r "$RELEASEDIR/clnrest-$VERSION"
cd ..
echo "Zip File Created"

echo "Building Docker Images"
for d in amd64 arm64v8; do
    echo "Bundling $d image"
    case "$d" in
        "arm64v8")
            PLATFORM="linux/arm64"
            ;;
        *)
            PLATFORM="linux/amd64"
            ;;
    esac
    docker buildx build --load --platform $PLATFORM -t "shahanafarooqui/clnrest:$VERSION-$d" -f Dockerfile .
    echo "Docker Image $d Built"
done

for d in amd64 arm64v8; do
    echo "Extracting Bineries for $d"
    docker create --name temp-container "shahanafarooqui/clnrest:$VERSION-$d"
    docker cp "temp-container:/release/cln_rest" "$RELEASEDIR/cln_rest.$VERSION-$d"
    docker cp "temp-container:/release/clnrest" "$RELEASEDIR/clnrest.$VERSION-$d"
    docker rm temp-container
    echo "Bineries Extracted for $d"
done

echo "Signing Release"
cd $RELEASEDIR
sha256sum * > SHA256SUMS
gpg -sb --armor SHA256SUMS
echo "Release Signed"
