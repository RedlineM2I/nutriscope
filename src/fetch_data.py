"""Téléchargement du parquet Open Food Facts depuis Hugging Face, avec vérification SHA-256."""
import hashlib
import urllib.error
import urllib.request

from tqdm import tqdm

from src.config import BASE_DIR
from src.console import pause_spinner

URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet?download=true"
DEST = BASE_DIR / ".." / "data" / "food.parquet"
PART = DEST.with_name(DEST.name + ".part")  # fichier en cours de téléchargement
CHUNK_SIZE = 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Gestionnaire qui refuse de suivre les redirections HTTP.

    Permet de lire les en-têtes de la réponse 302 elle-même (dont `X-Linked-Etag`).
    """

    def redirect_request(self, *args, **kwargs):
        """Renvoie None : la redirection n'est pas suivie et lève une `HTTPError`."""
        return None


def expected_sha256() -> str | None:
    """Renvoie le SHA-256 publié par Hugging Face pour le parquet.

    Il est lu dans l'en-tête `X-Linked-Etag` de la redirection vers le stockage
    des gros fichiers (LFS).

    Returns:
        Empreinte attendue, ou None si Hugging Face ne la fournit pas.
    """
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        headers = opener.open(urllib.request.Request(URL, method="HEAD")).headers
    except urllib.error.HTTPError as e:  # la redirection 302 arrive ici
        headers = e.headers
    etag = headers.get("X-Linked-Etag")
    return etag.strip('"') if etag else None


def download():
    """Télécharge le fichier parquet depuis l'URL et affiche une barre de progression.

    Le fichier est écrit dans `PART`, vérifié (SHA-256), puis renommé en `DEST` :
    `DEST` n'est jamais un fichier incomplet ou corrompu.

    Raises:
        RuntimeError: l'empreinte du fichier téléchargé ne correspond pas à celle
            publiée (le fichier `PART` est alors supprimé).
    """
    DEST.parent.mkdir(parents=True, exist_ok=True)
    expected = expected_sha256()
    sha = hashlib.sha256()

    # Le spinner du @timer est suspendu : il se disputerait la ligne avec la barre tqdm
    with pause_spinner(), urllib.request.urlopen(URL) as response, open(PART, "wb") as f:
        total = int(response.headers.get("Content-Length", 0)) or None
        with tqdm(total=total, unit="B", unit_scale=True, unit_divisor=1024, desc=DEST.name) as bar:
            for chunk in iter(lambda: response.read(CHUNK_SIZE), b""):
                f.write(chunk)
                sha.update(chunk)  # empreinte calculée au fil de l'eau : pas de relecture des 8 Go
                bar.update(len(chunk))

    if expected is None:
        print("⚠ SHA-256 non fourni par Hugging Face : fichier non vérifié")
    elif sha.hexdigest() != expected:
        PART.unlink()
        raise RuntimeError(f"Fichier corrompu : SHA-256 {sha.hexdigest()} au lieu de {expected}")

    PART.replace(DEST)  # renommage atomique : DEST passe directement de l'ancien au nouveau fichier
    print(f"Terminé : {DEST}")


if __name__ == "__main__":
    download()
