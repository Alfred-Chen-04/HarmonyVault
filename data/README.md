# data/

Large CSVs are not committed. Download them locally before running `scripts/setup_db.py`.

## Spotify Tracks (primary dataset)

Source: <https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db>

Steps:

1. Create a Kaggle account and accept the dataset's terms.
2. Download the archive (`archive.zip`) and extract `SpotifyFeatures.csv` into this directory.
3. The path should be `data/SpotifyFeatures.csv` (matches the default in `.env.example`).

To load a smaller subset during development, edit `SPOTIFY_LOAD_LIMIT` in `.env`.

## Synthetic data

`scripts/generate_synthetic.py` seeds Faker with a fixed random seed so repeated runs produce the same users, tags, projects, and collaborators. Adjust the constants at the top of that file to scale the dataset up or down for testing.

## Final submission

For the May 1 Canvas upload, include a Google Drive link inside `report/final_report.md` instead of zipping the CSV — the Kaggle data is ~150 MB and will inflate the submission beyond reasonable limits.
