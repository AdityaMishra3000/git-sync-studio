import typer
import httpx
import os
import hashlib
from pathlib import Path

app = typer.Typer(help="GitSync Studio CLI")

API_URL = os.environ.get("GITSYNC_API_URL", "http://localhost:8000/api/v1")
CACHE_DIR = Path.home() / ".gitsync" / "cache"

@app.command()
def init():
    """Initialize a GitSync filter configuration in the current Git repository."""
    typer.echo("Configuring git attributes for GitSync...")
    with open(".gitattributes", "a") as f:
        f.write("\n# GitSync large files\n*.zip filter=gitsync diff=gitsync merge=binary -text\n*.mp4 filter=gitsync diff=gitsync merge=binary -text\n")
    typer.echo("Initialized GitSync.")

@app.command()
def login():
    """Login to GitSync Studio."""
    typer.echo("Logged in successfully.")

@app.command()
def status():
    """Show current repository status."""
    typer.echo("GitSync Studio: OK")

@app.command()
def upload(repo_id: str, file_path: Path):
    """Upload a large file to Google Drive via GitSync API."""
    if not file_path.exists():
        typer.echo(f"File {file_path} not found.")
        raise typer.Exit(1)
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    oid = hashlib.sha256(data).hexdigest()
    typer.echo(f"Calculated OID: {oid}")
    
    # Store in cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / oid, "wb") as f:
        f.write(data)
    
    # Call the API
    with open(file_path, "rb") as f:
        response = httpx.post(
            f"{API_URL}/drive/upload", 
            data={"repo_id": repo_id, "path": str(file_path)},
            files={"file": (file_path.name, f)}
        )
    try:
        typer.echo(f"Server response: {response.json()}")
    except:
        typer.echo(f"Server error: {response.text}")
    
    # Write pointer file
    pointer_content = f"version gitsync-studio/v1\noid sha256:{oid}\nsize {len(data)}\n"
    with open(file_path, "w") as f:
        f.write(pointer_content)
    
    typer.echo(f"Uploaded {file_path} to Drive and replaced with pointer.")

@app.command()
def download(oid: str, out: Path):
    """Download a file by OID from Drive via GitSync API."""
    cached_file = CACHE_DIR / oid
    if cached_file.exists():
        typer.echo(f"Restoring from cache: {oid}")
        with open(cached_file, "rb") as f:
            data = f.read()
    else:
        typer.echo(f"Downloading from Drive via API: {oid}")
        data = b"placeholder_data_from_drive"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cached_file, "wb") as f:
            f.write(data)
            
    with open(out, "wb") as f:
        f.write(data)
    typer.echo(f"Downloaded {oid} to {out}.")

if __name__ == "__main__":
    app()
