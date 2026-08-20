import urllib.request
from pathlib import Path
from tqdm import tqdm

URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet?download=true"
DEST = Path(__file__).resolve().parents[2] / "data" / "food.parquet"

class TqdmUpTo(tqdm):
    def update_to(self, blocks=1, block_size=1, total_size=None):
        if total_size is not None:
            self.total = total_size
        self.update(blocks * block_size - self.n)

def download():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with TqdmUpTo(unit="B", unit_scale=True, unit_divisor=1024, desc=DEST.name) as bar:
        urllib.request.urlretrieve(URL, DEST, reporthook=bar.update_to)
    print(f"Terminé : {DEST}")

if __name__ == "__main__":
    download()