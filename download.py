import os
import math
import shutil
import requests
import mercantile
from PIL import Image
from rich.progress import track

# env variables
SATELLITE_ENDPOINT = "https://api.mapbox.com/v4/mapbox.satellite"
ELEVATION_ENDPOINT = "https://api.mapbox.com/v4/mapbox.terrain-rgb"
API_TOKEN = open("token", "r").read().split("\n")[0]
DATA_PATH = "data"
COORDINATES = {
    "top_left": {
        "latitude": 25.93,
        "longitude": -80.40,
    },
    "bottom_right": {"latitude": 25.62, "longitude": -80.04},
}


def create_data_paths():
    if os.path.exists(DATA_PATH):
        shutil.rmtree(DATA_PATH)
    os.mkdir(DATA_PATH)
    os.mkdir(f"{DATA_PATH}/satellite")
    os.mkdir(f"{DATA_PATH}/elevation")
    os.mkdir(f"{DATA_PATH}/composite")


def compute_tile_ranges(
    tl: dict[str, float], br: dict[str, float], z: int
) -> tuple[list[int]]:
    """
    computes tile ranges from top left and bottom right lat long coordinates of bounding box

    Args:
        tl (tuple[float]): top left lat/long coordinates
        br (tuple[float]): bottom right lat/long coordinates
        z (int): resolution of the tile ranges

    Returns:
        tuple[list[int]]: tuple of the X tile range and Y tile range
    """
    tl_tiles = mercantile.tile(tl["longitude"], tl["latitude"], z)
    br_tiles = mercantile.tile(br["longitude"], br["latitude"], z)
    x_tile_range = [tl_tiles.x, br_tiles.x]
    y_tile_range = [tl_tiles.y, br_tiles.y]
    return (x_tile_range, y_tile_range)


def retrieve_mapbox_images(
    x_tile_range: list[float], y_tile_range: list[float], z: int, kind: str
):
    assert kind in {"elevation", "satellite"}
    form = "png" if kind == "satellite" else "pngraw"
    endpoint = SATELLITE_ENDPOINT if kind == "satellite" else ELEVATION_ENDPOINT
    # index param used instead of enumeration so track bar works
    ix, iy = 0, 0
    for tx in track(
        range(x_tile_range[0], x_tile_range[1] + 1),
        description=f"downloading data: {kind}",
    ):
        for iy, ty in enumerate(range(y_tile_range[0], y_tile_range[1] + 1)):
            resp = requests.get(
                f"{endpoint}/{str(z)}/{str(tx)}/{str(ty)}@2x.{form}?access_token={API_TOKEN}",
                stream=True,
            )
            if resp.status_code == 200:
                with open(f"{DATA_PATH}/{kind}/{str(ix)}.{str(iy)}.png", "wb") as f:
                    resp.raw.decode_content = True
                    shutil.copyfileobj(resp.raw, f)
        ix += 1


def make_composite_images(
    x_tile_range: list[float], y_tile_range: list[float], kind: str
):
    assert kind in {"elevation", "satellite"}
    files = [f"{DATA_PATH}/{kind}/{f}" for f in os.listdir(f"{DATA_PATH}/{kind}")]
    images = [Image.open(f) for f in files]
    edge_length_x = x_tile_range[1] - x_tile_range[0]
    edge_length_y = y_tile_range[1] - y_tile_range[0]
    edge_length_x = max(1, edge_length_x)
    edge_length_y = max(1, edge_length_y)
    width, height = images[0].size
    total_width = width * edge_length_x
    total_height = height * edge_length_y
    composite = Image.new("RGB", (total_width, total_height))
    y_offset = 0
    for i in track(range(0, edge_length_x), description=f"creating composite: {kind}"):
        x_offset = 0
        for j in range(0, edge_length_y):
            tmp_img = Image.open(f"{DATA_PATH}/{kind}/{str(i)}.{str(j)}.png")
            composite.paste(tmp_img, (y_offset, x_offset))
            x_offset += width
        y_offset += height
    composite.save(f"{DATA_PATH}/composite/{kind}.png")


if __name__ == "__main__":
    # Set the web mercator zoom level.
    zoom = 13
    # get tile ranges
    x_tile_range, y_tile_range = compute_tile_ranges(
        COORDINATES["top_left"], COORDINATES["bottom_right"], zoom
    )
    create_data_paths()
    retrieve_mapbox_images(x_tile_range, y_tile_range, zoom, "satellite")
    retrieve_mapbox_images(x_tile_range, y_tile_range, zoom, "elevation")
    make_composite_images(x_tile_range, y_tile_range, "satellite")
    make_composite_images(x_tile_range, y_tile_range, "elevation")
