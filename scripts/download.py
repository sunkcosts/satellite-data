import os
import shutil
import requests
import mercantile
from rich.progress import track

# env variables
SATELLITE_ENDPOINT = "https://api.mapbox.com/v4/mapbox.satellite"
ELEVATION_ENDPOINT = "https://api.mapbox.com/v4/mapbox.terrain-rgb"
API_TOKEN = open("../token", "r").read().split("\n")[0]


def create_data_paths():
    if os.path.exists("../data"):
        shutil.rmtree("../data")
    os.mkdir("../data")
    os.mkdir("../data/satellite")
    os.mkdir("../data/elevation")


def compute_tile_ranges(tl: tuple[float], br: tuple[float], z: int) -> tuple[list[int]]:
    """
    computes tile ranges from top left and bottom right lat long coordinates of bounding box

    Args:
        tl (tuple[float]): top left lat/long coordinates
        br (tuple[float]): bottom right lat/long coordinates
        z (int): resolution of the tile ranges

    Returns:
        tuple[list[int]]: tuple of the X tile range and Y tile range
    """
    tl_tiles = mercantile.tile(tl[1], tl[0], z)
    br_tiles = mercantile.tile(br[1], br[0], z)
    x_tile_range = [tl_tiles.x, br_tiles.x]
    y_tile_range = [tl_tiles.y, br_tiles.y]
    return (x_tile_range, y_tile_range)


def retrieve_mapbox_images(
    tl: tuple[float], br: tuple[float], z: int, kind: str, save: str
):
    assert kind in {"elevation", "satellite"}
    form = "png" if kind == "satellite" else "pngraw"
    endpoint = SATELLITE_ENDPOINT if kind == "satellite" else ELEVATION_ENDPOINT
    x_tile_range, y_tile_range = compute_tile_ranges(tl, br, z)
    # index param used instead of enumeration so track bar works
    ix, iy = 0, 0
    for tx in track(range(x_tile_range[0], x_tile_range[1] + 1)):
        for iy, ty in enumerate(range(y_tile_range[0], y_tile_range[1] + 1)):
            resp = requests.get(
                f"{endpoint}/{str(z)}/{str(tx)}/{str(ty)}@2x.{form}?access_token={API_TOKEN}",
                stream=True,
            )
            if resp.status_code == 200:
                with open(f"{save}/{kind}/{str(ix)}.{str(iy)}.png", "wb") as f:
                    resp.raw.decode_content = True
                    shutil.copyfileobj(resp.raw, f)
        ix += 1


if __name__ == "__main__":
    # set the center point of the image
    LAT_LNG = [25.828782, -80.217522]
    # set the delta from the center point
    DELTA = 0.13
    # set the top left and bottom right bounding boxes
    TOP_LEFT = [LAT_LNG[0] + DELTA, LAT_LNG[1] - DELTA]
    BOTTOM_RIGHT = [LAT_LNG[0] - DELTA, LAT_LNG[1] + DELTA]
    # Set the resolution
    RESOLUTION = 13
    create_data_paths()
    retrieve_mapbox_images(TOP_LEFT, BOTTOM_RIGHT, RESOLUTION, "satellite", "../data")
    retrieve_mapbox_images(TOP_LEFT, BOTTOM_RIGHT, RESOLUTION, "elevation", "../data")
